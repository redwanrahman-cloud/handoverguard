# Demo video production

The recording harness captures one continuous, real run of the public AWS judge console at
1920×1080. It uses the narration waveform as the master timeline, drives actual approve/reject
actions, and switches briefly to the architecture diagram while the execution is explained.

Generated media belongs under `dist/video/` and is excluded from Git.

```bash
node tools/video/record-demo.cjs
```

For the submission master, use the high-quality frame pipeline instead of Playwright's
low-bitrate VP8 recorder:

```bash
HG_RECORD_HQ=1 node tools/video/record-demo.cjs
```

The preferred deliverable has no burned-in captions. Upload
`dist/video/handoverguard-brian-narration.srt` as a toggleable caption track. If a burned-in
accessible copy is needed, generate phrase-level captions with
`tools/video/compact-captions.cjs` and keep them in the lower safe area; never place full
sentences across the center of the product UI.

The raw WebM is then synchronized with `dist/video/handoverguard-brian-narration.mp3`, captions
are burned from `dist/video/handoverguard-brian-narration.srt`, and the result is exported as an
H.264/AAC MP4. Always inspect frames at multiple timestamps and verify that no credentials,
account IDs, callback tokens, or private data are visible.
