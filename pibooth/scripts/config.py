# -*- coding: utf-8 -*-

"""Script to view and modify configuration entries from the command line.
"""

import sys
import argparse
import ast
from pibooth.utils import LOGGER, configure_logging
from pibooth.config import PiConfigParser
from pibooth.plugins import create_plugin_manager
from pibooth.config.parser import DEFAULT

def list_config(config, section=None):
    """List all configuration entries.
    """
    for sect, options in DEFAULT.items():
        if section and sect.lower() != section.lower():
            continue
            
        print(f"\n[{sect}]")
        for name, value in options.items():
            current = config.get(sect, name)
            default = str(value[0])
            if current == default:
                print(f"  {name} = {current}")
            else:
                print(f"  {name} = {current}  (default: {default})")
            print(f"    {value[1]}")


def get_config_value(config, section, option):
    """Get and display a specific configuration value.
    """
    try:
        value = config.get(section, option)
        print(f"{value}")
        return True
    except KeyError:
        LOGGER.error(f"No configuration option [{section}][{option}]")
        return False


def set_config_value(config, section, option, value):
    """Set a configuration value.
    """
    try:
        # Try to convert the string value to a Python type
        try:
            value = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # Keep as string if not a valid Python literal
            pass
            
        # If it's a string that's not already quoted, add quotes
        if isinstance(value, str) and not (value.startswith('"') and value.endswith('"')):
            value = f'"{value}"'
            
        config.set(section, option, str(value))
        LOGGER.info(f"Updated [{section}][{option}] = {value}")
        return True
    except KeyError:
        LOGGER.error(f"No configuration option [{section}][{option}]")
        return False


def reset_config_value(config, section=None, option=None):
    """Reset configuration values to default.
    """
    if section and option:
        # Reset a specific option
        try:
            default_value = DEFAULT[section][option][0]
            config.set(section, option, str(default_value))
            LOGGER.info(f"Reset [{section}][{option}] to default: {default_value}")
            return True
        except KeyError:
            LOGGER.error(f"No configuration option [{section}][{option}]")
            return False
    else:
        # Generate a new default configuration
        config.save(default=True)
        LOGGER.info("Reset all configuration options to default values")
        return True


def main():
    """Application entry point.
    """
    parser = argparse.ArgumentParser(description="View and modify pibooth configuration entries.")
    
    parser.add_argument("--config-dir", "-c", default="~/.config/pibooth", 
                        help="Path to configuration directory (default: %(default)s)")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List configuration entries")
    list_parser.add_argument("section", nargs="?", help="Only list entries for specified section")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a configuration value")
    get_parser.add_argument("section", help="Configuration section")
    get_parser.add_argument("option", help="Configuration option name")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("section", help="Configuration section")
    set_parser.add_argument("option", help="Configuration option name")
    set_parser.add_argument("value", help="New value")
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset configuration to default values")
    reset_parser.add_argument("section", nargs="?", help="Configuration section to reset")
    reset_parser.add_argument("option", nargs="?", help="Configuration option to reset")
    
    args = parser.parse_args()
    
    configure_logging()
    plugin_manager = create_plugin_manager()
    config_file = PiConfigParser(f"{args.config_dir}/pibooth.cfg", plugin_manager)
    
    # Register plugins to load all possible configuration options
    plugin_manager.load_all_plugins(config_file.gettuple('GENERAL', 'plugins', 'path'),
                                   config_file.gettuple('GENERAL', 'plugins_disabled', str))
    
    # Update configuration with plugins ones
    plugin_manager.hook.pibooth_configure(cfg=config_file)
    
    result = False
    save_needed = False
    
    if args.command == "list":
        list_config(config_file, args.section)
        result = True
        
    elif args.command == "get":
        result = get_config_value(config_file, args.section, args.option)
        
    elif args.command == "set":
        result = set_config_value(config_file, args.section, args.option, args.value)
        save_needed = result
        
    elif args.command == "reset":
        result = reset_config_value(config_file, args.section, args.option)
        save_needed = result
        
    else:
        parser.print_help()
        
    if save_needed:
        config_file.save()
        
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
