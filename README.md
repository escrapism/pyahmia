![PyAhmia Logo](https://raw.githubusercontent.com/escrapism/pyahmia/refs/heads/master/img/ahmia.png)

**PyAhmia** uses Ahmia.fi to search for hidden services on the Tor network  
that match with a specified query. It works as a command-line interface tool  
and provides an easier way to export output to a CSV file.

![PyPI - Version](https://img.shields.io/pypi/v/pyahmia)
![PyPI - Downloads](https://img.shields.io/pepy/dt/pyahmia)
![Code Size](https://img.shields.io/github/languages/code-size/escrapism/pyahmia)
![Release Date](https://img.shields.io/github/release-date/escrapism/pyahmia)
![Build Status](https://img.shields.io/github/actions/workflow/status/escrapism/pyahmia/python-publish.yml)
![License](https://img.shields.io/github/license/escrapism/pyahmia)

## Features

- [x] Search Ahmia.fi from the command line
- [x] Export results to CSV
- [x] Enable/Disable routing requests through Tor
- [x] Return results in a clean readable format

## Installation

**PyAhmia** is available on PyPI and can be installed like so:

```commandline
pip install pyahmia
```

This will install `ahmia` and `pyahmia` as commands.

## Usage

To start searching, you can call `ahmia` (or `pyahmia`) with the specified search query.

*example*:

```commandline
ahmia QUERY
```

### Exporting output

PyAhmia only supports exporting data to csv files (for now), and in order to export, you'll need to specify the
`-e, --export` flag.
This will export your search results to a file named after your search query.

*example*:

```commandline
ahmia QUERY --export
```

### Routing through Tor

PyAhmia supports routing traffic through Tor. When this is enabled, it will use Ahmia's darknet url instead of the
clearnet variant.

To enable routing through Tor, you can call `ahmia` with the `-t, --use-tor` flag.
This assumes the tor service is running in the background, otherwise, the command will fail before you can say "hidden
wiki".

*example*:

```commandline
ahmia QUERY --use-tor
```

### Filtering results by time period

Results can be filtered by 3 time periods (day, week, month). By default, results will be taken from all time periods (
all). You can change this by using the `-p, --period` option, and pass the time period you want to get results from.

*example*:

```commandline
ahmia QUERY --period week
```

## In conclusion

Don't send too many requests with pyahmia. Be nice to the owners of Ahmia.fi :)

## Contributing

Contributions are welcome!
If you’d like to improve PyAhmia, fix a bug, or add a feature:

1. Fork the repository
2. Create a new branch for your changes
3. Commit and push your changes
4. Open a pull request

Please keep PRs focused and provide a clear description of the problem being solved. Bug reports and feature requests
are also appreciated, just open an issue.

## License

This project is licensed under the MIT License, see
the [LICENSE](https://github.com/escrapism/pyahmia/blob/master/LICENSE) file for details.


> [!Note]
> PyAhmia is not in any way affiliated with Ahmia.fi,
