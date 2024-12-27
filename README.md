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
* [lingua-language-detector | GitHub](https://github.com/pemistahl/lingua-py)

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

| Environment Variables          | Value Type  | Example             | Description                                                                        |
| ------------------------------ | ----------- | ------------------- | ---------------------------------------------------------------------------------- |
| `twitch_access_token`          | `str`       | `key`               | The OAuth Token for Twitch                                                         |
| `bot_administrators`           | `list[str]` | `user_one,user_two` | The list of users that is allowed to perform administrative commands               |
| `language_detection_model`     | `str`       | `adaptive`          | The language detection model to use when detecting language offline                |
| `language_detection_threshold` | `float`     | `0.75`              | The score threshold to accept when detecting the language via the `adaptive` model |
| `default_translation_engine`   | `str`       | `google`            | The default translation engine to use when no translation engine is specified      |
| `default_ignore_words`         | `list[str]` | `word_one,word_two` | List of words matching the whole message to be not translated by default           |
| `logging_level`                | `str`       | `info`              | The amount of information to be logged into log files                              |

##### Supported Language Detection Models
`legacy`
* Uses pre-trained models in the included libraries to identify supported languages; This detection model has the lowest detection accuracy 

`legacy-lazy`
* Uses pre-trained models in the included libraries to identify supported languages; This model utilizes the lazy loading mechanism and is loaded as needed.
* The lazy loading mechanism is only supported when `translation_engine` is set to `google` or `bing`

`adaptive`
* This models adaptively learns the words to needed to identify languages using Multinomial Naive Bayes algorithm
* This model is only supported when `translation_engine` is set to `google` or `bing` as the algorithmn relies results from these engine for learning
* Training data can be added to `resources/<language_id>.csv` to improve initial detection accuracy or to reduce the need to use external services

`adaptive-forced`
* Forces loading the adaptive model when using an unsupported translation engine
* Adaptive learning may not be available and accuracy is limited to known data only

When using other available but unsupported translation engine, language detection model will always default to `legacy`

#### Translation
_Note: Configuration for translation is per channel basis, and is not shared across all channels_

| Supported Key        | Value Type  | Example             | Description                                                                                                                                                         |
| -------------------- | ----------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `target_languages`   | `list[str]` | `en,ja`             | The target languages to be translated to; If the language of the message matches to any of target languages, it will be translated to the other specified languages |
| `ignore_languages`   | `list[str]` | `en,ja`             | The languages to ignore, when specified, the message in the specified language will be ignored                                                                      |
| `translation_engine` | `str`       | `google`            | The translation engine to use for translation, defaults to the environment variable `default_translation_engine` unless overridden                                  |
| `sanitize_emojis`    | `bool`      | `true`              | Remove emojis from text before sending for translation                                                                                                              |
| `sanitize_usernames` | `bool`      | `true`              | Remove usernames from text before sending for translation                                                                                                           |
| `ignore_words`       | `list[str]` | `word_one,word_two` | List of words matching the whole message to be not translated, defaults to the environment variable `default_ignore_words` unless overridden                        |
| `debug_mode`         | `bool`      | `true`              | Allow errors messages to be sent as messages by the chatbot                                                                                                         |
| `enabled`            | `bool`      | `true`              | Enable or disable the module for the current channel                                                                                                                |


