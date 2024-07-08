# TaTC is another Translation Chatbot for Twitch

TaTc is another Translation Chatbot for Twitch, built on various third parties libraries to provide real-time translations
on the live chat.  

**Disclaimer:**
* The chatbot may not function as expected on high volume channels due to external factors such rate limits
imposed by third parties provider
* Accuracy of the translation is not guaranteed, and translations are provided as it is from third parties providers

---
## Software Prerequisites
* Python 3.10 or later

## Credits

### Libraries:
* [TwitchIO | GitHub](https://github.com/PythonistaGuild/TwitchIO)
* [translators | GitHub](https://github.com/UlionTse/translators)
* [fast-langdetect | GitHub](https://github.com/LlmKira/fast-langdetect)

## Building from source

### Windows:
*Coming Soon*

### Linux/Mac:
```bash
# git clone https://github.com/rimu911/tatc
cd tatc/
/bin/bash "$(pwd)/scripts/build.sh"
```

---

## Releases
_Coming Soon_

---
## Usage Instructions

By default, the chatbot will always join the channel of the current user, or the owner of the OAuth Token.  
From there, the bot administrator can issue the `!join <channel>` command to join the specified channels.  
Further configuration can be done by the bot administrator, or the broadcaster (also known as the channel owner) by issuing the command `!config ...`
on their respective live chats.  
All configurations are tied to their respective channels, and is  not globally shared.

### Administrative Commands

Joins the specified channel.  
**Note: This command is only available to bot administrators**
```text
!join [<channel>|<channel_one>,<channel_two>,...]
```

Leaves the current channel, unless specified.  
**Note: Only bot administrators are allowed to specify channels**
```text
!leave [<empty>|<channel>|<channel_one>,<channel_two>,...]
```

### Available Global Commands
**Note: These commands are associated to the current which it is issued**

Set the value(s) associated with the specified key, multiple values should be delimited by ','
```text
!config <module> set <key> [<value>|<value_one>,<value_two>,...]
```

Retrieve the value(s) associated with the specified key
```text
!config <module> get <key>
```

Provides additional information associated with the specified key
```text
!config <module> info <key>
```

Remove the value(s) associated with the specified key
```text
!config <module> remove <key>
```

Enabling or disabling a module
```text
!config <module> enabled [true|false]
```

Enabling debug mode
```text
!config <module> debug_mode [true|false]
```

## Configuration

### Available Modules:
* Translation


### Twitch Chat Bot

Typical directory structure:
```text
<current_working_directory>
├── .env
├── bot.log
├── channels.json
├── tatc
└── translations.log
```

#### Environment Variables:
_Note: The following can be specified as an environment variable, or in `.env` within the current working directory_

| Environment Variables        | Value Type  | Example             | Description                                                                   |
|------------------------------|-------------|---------------------|-------------------------------------------------------------------------------|
| `twitch_access_token`        | `str`       | `key`               | The OAuth Token for Twitch                                                    |
| `bot_administrators`         | `list[str]` | `user_one,user_two` | The list of users that is allowed to perform administrative commands          | 
| `low_memory_mode`            | `bool`      | `true`              | Use lesser memory when performing language detection                          |
| `default_translation_engine` | `str`       | `google`            | The default translation engine to use when no translation engine is specified |
| `default_ignore_words`       | `list[str]` | `word_one,word_two` | List of words matching the whole message to be not translated by default      |
| `logging_level`              | `str`       | `info`              | The amount of information to be logged into log files                         |


#### Translation
_Note: Configuration for translation is per channel basis, and is not shared across all channels_

| Supported Key         | Value Type  | Example             | Description                                                                                                                                  |
|-----------------------|-------------|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `target_languages`    | `list[str]` | `en,ja`             | The target languages to be translated, by default, chat messages in the specified target languages will be ignored                           |
| `ignore_languages`    | `list[str]` | `en,ja`             | The languages to ignore, by default, chat messages in the specified target languages will be ignored                                         |
| `translation_engines` | `str`       | `google`            | The translation engine to use for translation, defaults to the environment variable `default_translation_engine` unless overridden           |
| `sanitize_emojis`     | `bool`      | `true`              | Remove emojis from text before sending for translation                                                                                       |
| `sanitize_usernames`  | `bool`      | `true`              | Remove usernames from text before sending for translation                                                                                    |
| `ignore_words`        | `list[str]` | `word_one,word_two` | List of words matching the whole message to be not translated, defaults to the environment variable `default_ignore_words` unless overridden | 
| `debug_mode`          | `bool`      | `true`              | Allow errors messages to be sent as messages by the chatbot                                                                                  |
| `enabled`             | `bool`      | `true`              | Enable or disable the module for the current channel                                                                                         |


