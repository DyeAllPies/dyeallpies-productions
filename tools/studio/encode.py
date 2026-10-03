"""ffmpeg and ffprobe for every format: the raw-frame writer, the gates, the copies, the join.

House rules (CLAUDE.md, machine-local skill): NVENC for the export, one NVENC encode at a time,
previews with libx264 on the CPU, `ffmpeg -v error -i out -f null -` on every delivered file.

The join without a re-encode (2026-09-12): appending the 2.5 s brand sting used to re-encode the
whole shot through NVENC (the join cost a full export). `concat_copy()` writes a concat-demuxer
list and copies both streams; the tail must match the shot's stream parameters, which
`sting_encode_args()` produces from a probe of the shot (same codec, profile, size, rate, pixel
format, a silent AAC track at the shot's sample rate and channel count). `concat_copy()` checks the
parameters before joining and refuses a mismatch instead of writing a file players will mis-decode.
"""
import json, os, subprocess, tempfile

NVENC = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "14", "-pix_fmt", "yuv420p"]
X264_PREVIEW = ["-c:v", "libx264", "-crf", "23", "-preset", "fast"]


def probe(path):
    """ffprobe -> {'video': {...}, 'audio': {...} or None, 'format': {...}}."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out); v = a = None
    for s in j["streams"]:
        if s["codec_type"] == "video" and v is None: v = s
        if s["codec_type"] == "audio" and a is None: a = s
    return {"video": v, "audio": a, "format": j.get("format", {})}


def frame_count(path):
    v = probe(path)["video"]
    if v.get("nb_frames"): return int(v["nb_frames"])
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return int(out.strip())


class RawWriter:
    """Pipe BGR uint8 frames into ffmpeg. `audio_from` copies that file's audio under the video (-shortest)."""

    def __init__(self, out, W, H, fps=30, audio_from=None, codec=None, extra=(), audio_inputs=(), audio_t=None):
        """audio_inputs: extra ffmpeg input arguments for a generated track (e.g. a lavfi anullsrc for a
        silent sting), limited to audio_t seconds; its encoder settings go in `extra`."""
        codec = list(codec or NVENC)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
        if audio_from:
            cmd += ["-i", audio_from, "-map", "0:v", "-map", "1:a?", "-c:a", "copy", "-shortest"]
        elif audio_inputs:
            ai = list(audio_inputs)
            if audio_t is not None:                                  # -t before the -i is an input option (limits the generated track)
                k = len(ai) - 1 - ai[::-1].index("-i"); ai = ai[:k] + ["-t", f"{audio_t:.3f}"] + ai[k:]
            cmd += ai + ["-map", "0:v", "-map", "1:a", "-shortest"]
        cmd += codec + list(extra) + ["-movflags", "+faststart", out]
        self.out = out; self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE); self.n = 0

    def write(self, frame_bgr):
        self.proc.stdin.write(frame_bgr.tobytes()); self.n += 1

    def close(self):
        self.proc.stdin.close(); self.proc.wait()
        return self.proc.returncode


def decode_check(path):
    """The delivery gate: a full decode with errors only. Returns (ok, stderr). It passes a SILENT file
    (2026-09-18: the finger web's exports had no audio track for a whole round because the upright master
    was made without one and `audio_from=` copied nothing), so print `streams()` next to it."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"], capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip(), r.stderr


def streams(path):
    """One line for the delivery report: the video stream, and the audio stream or NO AUDIO."""
    p = probe(path); v = p["video"]; a = p["audio"]
    s = f"video {v['codec_name']} {v['width']}x{v['height']} {v.get('nb_frames', '?')} frames"
    return s + (f", audio {a['codec_name']} {a['sample_rate']} Hz {a['channels']} ch" if a else ", NO AUDIO")


def mux_audio(video, audio_src, out, start=0.0, duration=None, bitrate="160k"):
    """Lay `audio_src`'s audio from `start` seconds under `video`'s video stream (copied, no re-encode; the
    audio re-encoded to AAC so the trim is sample-accurate). `duration` limits the audio read; every video
    frame is kept. NO -shortest here: with the audio trimmed to the video's length it ends an AAC frame early
    and -shortest then dropped the last video frame of both exports (2026-09-18). For an export rendered from a
    silent master: `start` is the export's first source frame over the frame rate."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", f"{start:.4f}"] + (["-t", f"{duration:.4f}"] if duration else [])
    cmd += ["-i", audio_src, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", bitrate, "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("mux failed: " + r.stderr)
    return out


def preview_720(src, out):
    """The phone copy, on the CPU so it never queues behind an NVENC export."""
    return subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "scale=720:1280"] + X264_PREVIEW +
                          ["-c:a", "copy", "-movflags", "+faststart", out]).returncode


def sting_encode_args(shot):
    """Encoder arguments that make a tail concat-copyable after `shot`: same video parameters, a silent
    AAC track shaped like the shot's audio (or none if the shot has none). Returns (video_args, audio_inputs, audio_args)."""
    p = probe(shot); v = p["video"]; a = p["audio"]
    if v["codec_name"] != "h264":
        raise ValueError(f"concat-copy join is written for h264 shots; {shot} is {v['codec_name']}")
    prof = {"Main": "main", "High": "high", "Baseline": "baseline", "Constrained Baseline": "baseline"}.get(v.get("profile"), "main")
    vid = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "14", "-pix_fmt", v["pix_fmt"], "-profile:v", prof,
           "-level", str(int(v["level"]) / 10.0), "-r", v["r_frame_rate"]]
    if a is None:
        return vid, [], ["-an"]
    ch = int(a["channels"]); layout = {1: "mono", 2: "stereo"}.get(ch, f"{ch}c")
    return vid, ["-f", "lavfi", "-i", f"anullsrc=r={a['sample_rate']}:cl={layout}"], ["-c:a", "aac", "-b:a", "160k", "-ar", a["sample_rate"], "-ac", str(ch)]


_MATCH_V = ("codec_name", "width", "height", "pix_fmt", "r_frame_rate", "profile")
_MATCH_A = ("codec_name", "sample_rate", "channels")


def concat_copy(parts, out):
    """Join MP4s without re-encoding (concat demuxer, -c copy). Refuses if the stream parameters differ."""
    probes = [probe(p) for p in parts]
    for i, q in enumerate(probes[1:], 1):
        for k in _MATCH_V:
            if q["video"].get(k) != probes[0]["video"].get(k):
                raise ValueError(f"{parts[i]}: video {k} {q['video'].get(k)} != {probes[0]['video'].get(k)} of {parts[0]}; re-encode it with sting_encode_args()")
        ha, hb = probes[0]["audio"] is not None, q["audio"] is not None
        if ha != hb:
            raise ValueError(f"{parts[i]}: audio present={hb} but {parts[0]} present={ha}")
        if ha:
            for k in _MATCH_A:
                if q["audio"].get(k) != probes[0]["audio"].get(k):
                    raise ValueError(f"{parts[i]}: audio {k} {q['audio'].get(k)} != {probes[0]['audio'].get(k)}")
    lst = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8", newline="\n")
    for p in parts:
        lst.write("file '" + os.path.abspath(p).replace("\\", "/").replace("'", "'\\''") + "'\n")
    lst.close()
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst.name, "-c", "copy",
                            "-movflags", "+faststart", out], capture_output=True, text=True)
    finally:
        os.remove(lst.name)
    if r.returncode != 0:
        raise RuntimeError("concat failed: " + r.stderr)
    return r.stderr
