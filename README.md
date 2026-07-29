# IPTV

## Disclaimer

This program is just a demonstration. **It's not intended** for personal purpose.

## What is this?

IPTV is a simple Python 3 program that lets you crawl search engines to analyze sites streaming TV programs.

## Ethical Dilemma

Using this program for unauthorized access or illegal purposes is prohibited.

## How to run using Docker (GHCR)

You can run IPTV directly using Docker without installing local Python dependencies:

```bash
docker run -it --rm ghcr.io/jsanderstechnologies/iptv:latest
```

### Docker Compose Example

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  iptv:
    image: ghcr.io/jsanderstechnologies/iptv:latest
    container_name: iptv
    stdin_open: true
    tty: true
    restart: unless-stopped
    volumes:
      - ./output:/app/iptv/output
```

Run with Docker Compose:

```bash
docker compose run --rm iptv
```

### Build Docker Image Locally

```bash
docker build -t iptv:latest .
docker run -it --rm iptv:latest
```

## How to run locally (CLI version)

* Clone the repository: `git clone https://github.com/jsanderstechnologies/IPTV.git`
* `cd` into `iptv`
* Install dependencies: `pip install -r requirements.txt`
* Run: `python iptv.py`

## Compatibility

This program works on Windows, Linux, macOS, and BSD with Python 3.11+.

## License

See [the license](LICENSE) for further details.

## Contributing

Contributions are welcome and much appreciated, please read the [contributing guide](CONTRIBUTING.md) for further information.
