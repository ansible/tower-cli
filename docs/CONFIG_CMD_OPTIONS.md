## key-value options available for `tower-cli config <key> <value>` command
| *Key*            | *Value Type/Default*                                  | *Description*                                                                                                                                              |
|------------------|-------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `color`          | Boolean/'true'                                        | Whether to use colored output for highlighting or not.                                                                                                     |
| `format`         | String with options ('human', 'json', 'yaml')/'human' | Output format. The "human" format is intended for humans reading output on the CLI; the "json" and "yaml" formats provide more data.                       |
| `host`           | String/'127.0.0.1'                                    | The location of the Ansible Tower host. HTTPS is assumed as the protocol unless "http://" is explicitly provided.                                          |
| `password`       | String/''                                             | Password to use to authenticate to Ansible Tower.                                                                                                          |
| `username`       | String/''                                             | Username to use to authenticate to Ansible Tower.                                                                                                          |
| `verify_ssl`     | Boolean/'true'                                        | Whether to force verified SSL connections.                                                                                                                 |
| `verbose`        | Boolean/'false'                                       | Whether to show information about requests being made.                                                                                                     |
| `description_on` | Boolean/'false'                                       | Whether to show description in human-formatted output.                                                                                                     |
| `certificate`    | String/''                                             | Path to a custom certificate file that will be used throughout the command. Ignored if `--insecure` flag if set in command or `verify_ssl` is set to false |

## Environment Variables
All of the above options can also be set using environment variables. The default behavior is to allow environment variables to override your tower-cli.cfg settings, but they will not override config values that are passed in on the command line at runtime. Below is a table of the available environment variables.
## Variable Mapping
| *Environment Variable* | *Tower Config Key* |
|------------------------|--------------------|
| `TOWER_COLOR`          | `color`            |
| `TOWER_FORMAT`         | `format`           |
| `TOWER_HOST`           | `host`             |
| `TOWER_PASSWORD`       | `password`         |
| `TOWER_USERNAME`       | `username`         |
| `TOWER_VERIFY_SSL`     | `verify_ssl`       |
| `TOWER_VERBOSE`        | `verbose`          |
| `TOWER_DESCRIPTION_ON` | `description_on`   |
| `TOWER_CERTIFICATE`    | `certificate`      |

## Notes
* Under the hood we use the SSL functionality of requests, however the current requests version has checkings on a deprecated SSL certificate field `commonName` (deprecated by RFC 2818). In order to prevent any related usage issues, please make sure to add `subjectAltName` field to your own certificate in use. We will update help docs as soon as changes are made on the requests side.
