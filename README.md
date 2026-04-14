# Lime-translate

[![Version](https://img.shields.io/pypi/v/lime-translate.svg?maxAge=86400)](https://pypi.org/project/lime-translate/)
[![Supported Versions](https://img.shields.io/pypi/pyversions/lime-translate.svg)](https://pypi.org/project/lime-translate)

Lime-translate is a Python library that lets survey designers and professional translators work together, by converting LimeSurvey survey files into formats compatible with computer-assisted translation (CAT) software, and back again.

# Installation

`pip install lime-translate`

# Usage example

Bob creates a survey in Limesurvey, in English. He wants to have this questionnaire translated to French by a professional translator, Alice, who generally uses computer-assisted translation (CAT) software. As the survey is particularly complex, using CAT software would be much more quick and effective than using the native Limesurvey "quick translation" interface.

Bob creates an export of his survey to the LSS format. However, he and Alice quickly realize that this format is not compatible with the CAT software Alice uses. Therefore, Bob converts the LSS file to the CAT-friendly XLIFF format, using the lime-translate package:


```
import lime_translate as lt
lss_file_path = "./bob_survey/source_english.lss"
xliff_files = lt.lss_to_xliff(lss_file_path=lss_file_path)
target_fr_path = "./bob_survey/translation_files/to_translate/english_to_french.xliff"
with open(target_fr_path, "wb") as f:
    f.write(xliff_files["fr"])
```

Bob then transmits the new "english_to_french.xliff" file to Alice for translation.

Alice translates the XLIFF file in her CAT tool. Once it's done, she transmits the translated XLIFF file back to Bob. Bob then integrates the translation into the original LSS file, using the following code:

```
import lime_translate as lt
original_LSS_path = "./bob_survey/source_english.lss"
xliff_file_path = "./bob_survey/translation_files/translated/english_to_french.xliff"
updated_lss = lt.xliff_to_LSS(xliff_file_path, original_LSS_path)
with open("./bob_survey/translated/bilingual_en_fr.lss", "wb") as f:
    f.write(updated_lss)
```

Tadam! Bob will then be able to immediately import the resulting translated survey file ("bilingual_en_fr.lss") into Limesurvey.


# Current features

- conversion from LSS to XLIFF
- reintegrating a translated XLIFF file into a LSS file

This is an alpha version, so use it at your own risks!


## Exporting an LSS file from Limesurvey

To ensure your LSS file will work seamlessly with `lime-translate`, before [exporting the LSS file](https://www.limesurvey.org/manual/Display/Export_survey) from Limesurvey, you must [add your target language to the "additional languages" section](https://www.limesurvey.org/manual/Multilingual_survey) in the Limesurvey admin interface.

# Motivation

Limesurvey is an open-source statistical survey web application. It already offers a translation interface for multilingual surveys, but this translation interface is quite rudimentary compared to the features offered by modern computer-assisted translation tools (OmegaT, weblate, etc). In addition, Limesurvey currently does not offer an export format directly compatible with these CAT tools.

The `lime-translate` package is meant to fill this current compatibility gap between Limesurvey and computer-assisted translation tools.


# Limitations, compatibility with Limesurvey versions, etc.

While it is planned to support more recent versions of Limesurvey, the package current version is only compatible with LSS files exported from Limesurvey 3.x.

The only supported export format is XLIFF, while the package is also planned to support other formats in the future.

This is an alpha version, initially developed as an experiment for a one-time translation project. While it worked quite well for this specific project, it has not been tested extensively. The package is also missing a proper documentation, though a relatively straightforward usage example is provided above.

Any feedback is welcome, but use it at your own risks!
