**PyAhmia** uses Ahmia.fi to search for hidden services on the Tor network
that match with a specified query, it works as a command-line interface tool and provides an easier way to export output
to a csv file.

## Features

- Search Ahmia.fi from the command line
- Export results to CSV
- Route requests through Tor
- Limit or expand result count

## Example output

```
✔ Routing traffic through Tor                                                       _cli.py:63
✔ Showing 20 of 1004 results for osint                                              _cli.py:78
╭────────────────────────────────────────────────────────────────────────────────────────────╮
│ OSINT | Kikuri Knowledge Base                                                              │
│ ────────────────────────────────────────────────────────────────────────────────────────── │
│ No description provided                                                                    │
│ kikurizsbpb7ar4ozrzogt6nre3j7s7mccqwxeg3jvppyik2aa475lqd.onion — 3 weeks, 1 day            │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────────────────────────────────────────────╮
│ OSINT - #1 Mobile Hacker For Hire                                                          │
│ ────────────────────────────────────────────────────────────────────────────────────────── │
│ No description provided                                                                    │
│ torzcd47rw4qh36g4yqxvv2tmifgmu6jjalkyqz4e4lzzwtfdfc7qaqd.onion — 3 weeks                   │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
...
```

## Installation

**PyAhmia** is available on PyPI and can be installed like so:

```commandline
pip install pyahmia
```

This will install `ahmia` and `pyahmia` as commands.

## Usage

To start searching, you can call `ahmia` (or `pyahmia`) with the specified search query:

```commandline
ahmia QUERY
```

### Exporting output

PyAhmia only supports exporting data to csv files (for now), and in order to export, you'll need to specify the
`-e, --export` flag.
This will export your search results to a file named after your search query. E.g.,:

```commandline
ahmia QUERY --export
```

### Routing through Tor

PyAhmia supports routing traffic through Tor. When this is enabled, it will use Ahmia's darknet url instead of the
clearnet variant.

To enable routing through Tor, you can call `ahmia` with the `--use-tor` flag.
This assumes the tor service is running in the background, otherwise, the command will fail before you can say "hidden
wiki". E.g.,:

```commandline
ahmia QUERY --use-tor
```

### Limiting output

By default, pyahmia prints 20 results, but will also show the total amount of results that
were found for the specified query. You can change this by using the `-l, --limit` option and pass a number for how many
results you want to print. E.g.,:

```commandline
ahmia QUERY --limit 50
```

> [!Note]
> If the total number of results found is equal to the specified limit or more than that, then you'll see exactly that
> many.

## In conclusion

Don't send too many requests with pyahmia. Be nice to the owners of Ahmia.fi :)

## Contributing

Contributions are welcome!
If you’d like to improve PyAhmia, fix a bug, or add a feature:

* Fork the repository
* Create a new branch for your changes
* Commit and push your changes
* Open a pull request

Please keep PRs focused and provide a clear description of the problem being solved. Bug reports and feature requests
are also appreciated, just open an issue.

## License

This project is licensed under the MIT License, see
the [LICENSE](https://github.com/escrapism/pyahmia/blob/master/LICENSE) file for details.


> [!Note]
> PyAhmia is not in any way affiliated with Ahmia.fi,