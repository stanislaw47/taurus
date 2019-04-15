import argparse
import pkg_resources

from taurus import Release


def _make_parser():
    """
    Create main Taurus parser obejct with common options
    """
    # TODO: fine tune those options


    help_tauruslog = "taurus log level. Allowed values are (case insensitive): critical, "\
                     "error, warning/warn, info, debug, trace"
    help_tangohost = "Tango host name (either HOST:PORT or a Taurus URI, e.g. tango://foo:1234)"
    help_tauruspolling = "taurus global polling period in milliseconds"
    help_taurusserial = "taurus serialization mode. Allowed values are (case insensitive): "\
        "serial, concurrent (default)"
    help_rcport = "enables remote debugging using the given port"
    help_formatter = "Override the default formatter"

    parser = argparse.ArgumentParser(description="Taurus main launcher")
    parser.add_argument("-v", "--version", action="version", version=Release)

    main_group = parser.add_argument_group(title="Common Taurus options",
                                           description="Basic options present in any taurus application")
    main_group.add_argument("--taurus-log-level",
                            choices=["critical", "error", "warning", "info", "debug", "trace"],
                            metavar="LEVEL",
                            default="info",
                            help=help_tauruslog)
    main_group.add_argument("--taurus-polling-period",
                            type=int,
                            metavar="PERIOD",
                            help=help_tauruspolling)
    main_group.add_argument("--taurus-seriallization-mode",
                            choices=["TangoSerial", "Serial", "Concurrent"],
                            metavar="SERIAL",
                            default="Concurrent",
                            help=help_taurusserial)
    main_group.add_argument("--tango-host",
                            help=help_tangohost)
    main_group.add_argument("--remote-console-port",
                            type=int,
                            metavar="PORT",
                            help=help_rcport)
    main_group.add_argument("--default-formatter",
                            metavar="FORMATTER",
                            help=help_formatter)

    return parser


def _load_subcommands(parser):
    """
    Load subcommands to given parser from entrypoint
    """
    subparsers = parser.add_subparsers(dest='subcommand')

    for ep in pkg_resources.iter_entry_points("taurus.cli.subcommands"):
        ep.load()(subparsers)


def main():
    parser = _make_parser()
    _load_subcommands(parser)
    args = parser.parse_args()
    args.cmd(args)


if __name__ == '__main__':
    main()
