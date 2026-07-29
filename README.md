# IPTV

## Disclaimer

This program is just a demonstration. **It's not intended** for personal purpose.

## What is this?

IPTV is a Python 3 web & CLI application that lets you crawl search engines to analyze IPTV servers.

## Ethical Dilemma

Using this program for unauthorized access or illegal purposes is prohibited.

## Web Interface

The application now includes a modern, responsive web interface!

### Running with Docker (Web UI)

```bash
docker run -d -p 5000:5000 --name iptv ghcr.io/jsanderstechnologies/iptv:latest
```

Open your browser and navigate to: `http://localhost:5000`

### Running with Docker Compose

```yaml
version: '3.8'

services:
  iptv:
    image: ghcr.io/jsanderstechnologies/iptv:latest
    container_name: iptv
    ports:
      - "5000:5000"
    restart: unless-stopped
    volumes:
      - ./output:/app/iptv/output
```

Run with:

```bash
docker compose up -d
```

## Running CLI Version

If you prefer running the interactive command-line interface instead of the web server:

```bash
docker run -it --rm ghcr.io/jsanderstechnologies/iptv:latest python iptv.py
```

## Running Locally

* Clone the repository: `git clone https://github.com/jsanderstechnologies/IPTV.git`
* `cd` into `iptv`
* Install dependencies: `pip install -r requirements.txt`
* Run Web UI: `python app.py`
* Or run CLI: `python iptv.py`

## License

See [the license](LICENSE) for further details.
