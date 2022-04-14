---
Title: 'Installation'
Date: '2022-04-11'
---

Local installation without docker

<!--more-->

## Source Code

- latest release from the [release page](https://github.com/csf-ngs/hinkskalle/tags) and unpack

## Required Python Packages

```
cd backend/
# with sqlite only
pip install .
# or with postgres
pip install '.[postgres]'
```

## Singularity Binaries

Set up singularity according to the [instructions on sylabs.io](https://sylabs.io/docs/#singularity)

It is required only for checking image signatures and showing the singularity
definition file on the web.

The singularity binary should end up in `$PATH` so that Hinkskalle can find it.
`/usr/local/bin`, the default, is usually fine.

## Configuration

Hinkskalle reads its configuration from JSON files. By default it looks for

- `conf/config.json`
- `conf/secrets.json` (optional)

My recommendation is to put passwords etc. in an extra file (which is in
[.gitignore](.gitignore)) to make it harder to accidentally commit your
credentials.

See [configuration](../configuration) for valid configuration options.