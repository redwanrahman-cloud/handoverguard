# Demo video production

The recording harness captures one continuous, real run of the public AWS judge console at
1920×1080. It uses the narration waveform as the master timeline, drives actual approve/reject
actions, and switches briefly to the architecture diagram while the execution is explained.

Generated media belongs under `dist/video/` and is excluded from Git.

```bash
node tools/video/record-demo.cjs
```

The raw WebM is then synchronized with `dist/video/handoverguard-brian-narration.mp3`, captions
are burned from `dist/video/handoverguard-brian-narration.srt`, and the result is exported as an
H.264/AAC MP4. Always inspect frames at multiple timestamps and verify that no credentials,
account IDs, callback tokens, or private data are visible.
