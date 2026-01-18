"""Django management command for address autocomplete."""

from django.core.management.base import BaseCommand

from geoaddress.helpers import addresses_autocomplete


class Command(BaseCommand):
    """Autocomplete addresses using geoaddress providers."""

    help = "Autocomplete addresses using geoaddress providers"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'query',
            type=str,
            help='Search query string',
        )
        parser.add_argument(
            '--provider',
            type=str,
            help='Provider name filter',
        )
        parser.add_argument(
            '--first',
            action='store_true',
            help='Return first result only',
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'terminal'],
            help='Output format',
        )
        parser.add_argument(
            '--raw',
            action='store_true',
            help='Show raw response',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        query = options['query']
        provider = options.get('provider')
        first = options.get('first', False)
        output_format = options.get('format', 'json')
        raw = options.get('raw', False)

        kwargs = {}
        if provider:
            kwargs['attribute_search'] = {'name': provider}

        try:
            results = addresses_autocomplete(query, first=first, **kwargs)

            if isinstance(results, dict):
                for provider_name, result in results.items():
                    self.stdout.write(f"\n=== {provider_name} ===")
                    if isinstance(result, dict) and 'provider' in result:
                        provider_obj = result['provider']
                        response = provider_obj.response('addresses_autocomplete', raw=raw, format=output_format)
                        self.stdout.write(response)
                    else:
                        self.stdout.write(str(result))
            elif isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and 'provider' in result:
                        provider_obj = result['provider']
                        self.stdout.write(f"\n=== {provider_obj.name} ===")
                        response = provider_obj.response('addresses_autocomplete', raw=raw, format=output_format)
                        self.stdout.write(str(response))
                    else:
                        self.stdout.write(str(result))
            else:
                self.stdout.write(str(results))

        except Exception as e:
            self.stderr.write(f"Error: {e}")
            return
