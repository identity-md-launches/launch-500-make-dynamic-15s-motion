# Swarm Pepe — 15-second motion study

The finished video is **[artifacts/video.mp4](artifacts/video.mp4)**. It is a kinetic identity piece built from actual 24 × 24 SVG artwork in the [Swarm Pepe OpenSea collection](https://opensea.io/collection/swarm-pepe). The sequence moves through a signal intro, a hero portrait, pixel macro, three-card lineup, tile swarm, closeups, and a collection lockup.

## Deliverable

| Property | Value |
| --- | --- |
| Runtime | 15.000 seconds |
| Picture | 1280 × 720, 30 fps, H.264, yuv420p |
| Audio | Original synthesized 128 BPM stereo score, AAC, 44.1 kHz, 192 kb/s target |
| Container | MP4, fast-start metadata for browser playback |
| Size | 5,249,606 bytes |

## Sources and reproduction

- Original collection artwork was downloaded from the NFT media URLs exposed by the OpenSea page on 2026-09-30. The SVGs used in the film are in `assets/`; their collection media URLs are recorded in `assets/source_urls.tsv`.
- `assets/fonts/` contains Anton and Space Mono under their bundled SIL Open Font Licenses.
- `src/render.py` contains all animation, layout, audio synthesis, and encoding steps. Pillow and the FFmpeg command-line tools are included as ordinary files in `tools/`, so the source can be rendered without downloading Python packages or binaries. From the repository root: `PYTHONPATH=tools/python python3 src/render.py`.

## Verification and limits

FFprobe reports one H.264 `yuv420p` stream at 1280 × 720 and one stereo AAC stream at 44.1 kHz. FFmpeg decoded the complete output without errors. The score peaks at approximately −0.6 dBFS.

This is an independent motion study, not an official collection trailer. The design uses a curated selection of NFTs available on the collection page at capture time; it does not depict every token. Source art remains deliberately pixelated. The portrait artwork and collection wording reflect the 2026-09-30 capture and may differ from the current page. The portable source bundle targets this Linux runtime; a different operating system may need its own FFmpeg and Pillow binaries.
