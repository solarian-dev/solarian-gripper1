# solarian-umi-slim

A plugin for the Solarian robotics framework.

## Installation

```bash
pip install solarian-umi-slim
```

Or install from source:

```bash
cd solarian-umi-slim
pip install -e .
```

## Usage

After installation, the plugin is discovered by Solarian through the entry
points declared in `pyproject.toml`. Import the classes it provides directly,
for example:

```python
from solarian_umi_slim.actuator import UmiSlimServo
```

## Development

Add new component types to this plugin with:

```bash
solarian create-plugin <type> umi-slim
```

where `<type>` is one of: `actuator`, `sensor`, `module`, `robot`, `command`, `policy`.
