# Installation

```sh
sudo pacman -S python-pipx
pipx install git+https://github.com/iagocanalejas/autocana.git
pipx runpip autocana install git+https://github.com/iagocanalejas/pyutils.git@master
```

# Configuration

Running any command will ensure a configuration file exists in `~/.config/autocana/config.yaml`. If it doesn't it will create it.

You can also run the setup command to create or update the configuration file.

```sh
usage: AutoCana setup [-h] [-i] [--last-invoice LAST_INVOICE]

options:
  -i, --iterative                 Iteractive tool setup.
  --last-invoice LAST_INVOICE     Last invoice number used.
```

# Invoicing

Running this command will generate an invoice for the specified month using the template in `./autocana/templates/invoice.docx`.

Command can be run as follow with all the options.

```sh
usage: AutoCana invoice [-h] [-r RATE] [-d DAYS] [-m MONTH] [-o OUTPUT] [--output-dir OUTPUT_DIR]

options:
  -d, --days DAYS               Number of days to invoice. [20]
  -m, --month MONTH             Month to invoice (1-12). [current]
  -r, --rate RATE               Rate applied to the current invoice.
  -o, --output OUTPUT           Output file name.
  --output-dir OUTPUT_DIR       Output folder for the generated invoice.
```

### Example

```sh
autocana invoice -d 20 -o invoice.pdf --output-dir ~/Downloads
```

# TSH

Running the command will generate a TSH (Time Sheet) for the specified month using the template in `./autocana/templates/tsh.xlsx`.

Command can be run as follow with all the options.

```sh
usage: AutoCana tsh [-h] [-m MONTH] [-s [SKIP ...]] [-o OUTPUT] [--output-dir OUTPUT_DIR]

options:
  -m, --month MONTH             Month to TSH (1-12).
  -s, --skip [SKIP ...]         Days to skip in the TSH.
  -o, --output OUTPUT           Output file name.
  --output-dir OUTPUT_DIR       Output folder for the generated TSH.
```

### Example

```sh
autocana tsh -s 10 11 12 --output-dir ~/Downloads
```

# Init Library

Running the command will clone the template [repository](https://github.com/iagocanalejas/python-template) and make all the required changes to it.

Command can be run as follow with all the options.

```sh
usage: AutoCana newlibrary [-h] [--minpy MINPY] [--maxpy MAXPY] [--venv] project_name

positional arguments:
  project_name   Name of the project.

options:
  --minpy MINPY      Minimun version of python for the project. [3.12]
  --maxpy MAXPY      Maximun version of python for the project.
  --venv             Creates a new environment for the project.
```

### Example

```sh
autocana newlibrary myproject --minpy 3.13 --maxpy 3.14 --venv
```
