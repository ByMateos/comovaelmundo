import json, os, subprocess
D = "/tmp/claude-0/-home-claude/3f8f79a9-c46c-53fb-baec-2bfb3165bcc1/scratchpad/frames"
OUT = "/home/claude/canal/video1/video1_animado_por_que_todo_es_mas_caro.mp4"
lines, total, last = [], 0.0, None
for i in range(1, 17):
    for name, d in json.load(open(f"{D}/s{i:02d}.json")):
        lines.append(f"file '{D}/{name}'\nduration {d:.4f}")
        total += d
        last = name
lines.append(f"file '{D}/{last}'")
open(f"{D}/concat.txt", "w").write("\n".join(lines) + "\n")
print("total seconds", round(total, 1))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{D}/concat.txt",
                "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=48000:cl=stereo",
                "-vf", "fps=25,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("ok", OUT)
