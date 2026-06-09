# Privacy Policy

_Last updated: 7 June 2026_

scale-av-cutter ("the Tool") is an open-source command-line tool used by
Southern California Linux Expo (SCALE) volunteers to upload recorded conference
talks to a YouTube channel that the operator controls. This policy explains what
data the Tool accesses through YouTube API Services and how that data is handled.

The Tool uses YouTube API Services. By using it you agree to the
[YouTube Terms of Service](https://www.youtube.com/t/terms). Google's handling of
any data it receives is described in the
[Google Privacy Policy](https://policies.google.com/privacy).

## What the Tool accesses

The Tool authenticates with a single Google Account chosen by the operator using
OAuth 2.0, requesting only the
`https://www.googleapis.com/auth/youtube.upload` scope. With this scope it:

- uploads video files to the operator's own YouTube channel (`videos.insert`), and
- sets a thumbnail on each uploaded video (`thumbnails.set`).

The Tool does not read, collect, or process any other account's YouTube data. It
does not access viewer information, analytics, comments, subscriber data, or any
personal data of third parties.

## What the Tool stores

All data is stored locally on the machine the operator runs the Tool on. The Tool
does not operate a server and does not transmit data to anyone other than Google's
YouTube API.

- **OAuth credentials**: after authorization, an OAuth token (client ID, client
  secret, and refresh token) is saved to a local credentials file so the operator
  does not have to re-authorize on every run. Saving can be disabled with the
  `--no-save-token` flag.
- **Upload progress**: a local file records which talks have already been uploaded
  so re-runs can skip them. It contains talk identifiers and paths only, no
  personal data. Saving can be disabled with the `--no-save-progress` flag.

## Sharing

The Tool does not sell, share, or transfer any data to third parties. The only
external service it communicates with is the YouTube Data API.

## Retention and deletion

Stored data lives only in the local files described above. To delete it, remove
the credentials and progress files (by default `credentials.json` and
`progress.json`). To revoke the Tool's access to the authorized Google Account at
any time, visit your
[Google Account permissions](https://myaccount.google.com/permissions).

## Changes

This policy may be updated; material changes will be reflected in the
"Last updated" date above.
