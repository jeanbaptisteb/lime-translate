# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 08:45:07 2026

@author: jb.bertrand
"""



from lxml import etree, html
from collections import OrderedDict
import copy

XLIF_NS = "urn:oasis:names:tc:xliff:document:1.2"
NSMAP = {None: XLIF_NS}
translatable_sections = OrderedDict([("surveys_languagesettings", [
                                    "surveyls_title",
                                    "surveyls_description",
                                    "surveyls_welcometext",
                                    "surveyls_endtext",
                                    "surveyls_email_invite_subj",
                                    "surveyls_email_invite",
                                    "surveyls_email_remind_subj",
                                    "surveyls_email_remind",
                                    "surveyls_email_register_subj",
                                    "surveyls_email_register",
                                    "surveyls_email_confirm_subj",
                                    "surveyls_email_confirm",
                                    "email_admin_notification_subj",
                                    "email_admin_notification",
                                    "email_admin_responses_subj",
                                    "email_admin_responses",
                                    "surveyls_policy_notice",
                                    "surveyls_policy_error",
                                    "surveyls_policy_notice_label",
                                    ]),
                        ("groups",["group_name",
                                  "description"]),


                       ("questions",["question",
                                    "help",
                                    ]),
                       ("question_attributes",["value"]),
                       ("subquestions",["question",
                                       "help"]),

                       ("answers",["answer"]),
                       ("quota_languagesettings", ["quotals_message"])
                       ] )




def create_parser():
    parser = etree.XMLParser(recover=True,
                             resolve_entities=False,
                             strip_cdata=False)
    return parser

def validate_element(element, section, identifier=""):
    required_keys = {
        "surveys_languagesettings": ["field", "section"],
        "quota_languagesettings": ["field", "section"],
        "groups": ["gid", "field", "section"],
        "questions": ["gid", "qid", "field", "section"],
        "question_attributes": ["qid", "attribute", "field", "section"],
        "subquestions": ["gid", "parent_qid", "qid", "field", "section"],
        "answers": ["qid", "code", "field", "section"]
    }

    if section not in required_keys:
        raise ValueError(f"Unknown section: {section}")

    for key in required_keys[section]:
        if key not in element:
            raise ValueError(f"Missing required key '{key}' in element for section '{section}', id: {identifier}")

def lss_to_xliff(lss_file_path,
                 target_id_to_keep=[],
                 target_group_id_to_keep=[]):
    # Parse the LSS file
    tree = etree.parse(lss_file_path)
    root = tree.getroot()
    # survey_id = root.find("surveys/rows/row/sid").text
    source_lang = root.find("surveys/rows/row/language").text
    target_languages = root.find("surveys/rows/row/additional_languages").text.split(" ")


    def xpath_text(xpath):
        return [element.text if element.text is not None else "" for element in root.xpath(xpath)]

    new_order = []
    #first, surveys_languagesettings
    for field in translatable_sections["surveys_languagesettings"]:


        texts = [] #root.xpath(f"//{field}/text()")
        for elem in root.xpath(f"//{field}"):
            text = elem.text if elem.text is not None else ""
            texts.append(text)
        langs = root.xpath("//surveyls_language/text()")
        # dict_settings = {}
        dict_settings = {lang:txt for txt, lang in zip(texts, langs)}
        if dict_settings:
            for target_language in target_languages:
                target_lang_exist = bool(root.xpath(f"//surveys_languagesettings/rows/row[surveyls_language='{target_language}']"))
                if target_lang_exist is False:
                    dict_settings[target_language] = ""


            dict_settings["field"] = field
            dict_settings["section"] = "surveys_languagesettings"
            try:
                validate_element(dict_settings, dict_settings["section"])
            except ValueError as e:
                #let's not make it a blocking error - for the moment at least
                print(f"Validation error: {e}")

            new_order.append(dict_settings)

    #2: quotas
    for field in translatable_sections["quota_languagesettings"]:


        quota_unique_ids = list(set(root.xpath("//quotals_quota_id/text()")))

        field = "quotals_message"
        for quota_id in  quota_unique_ids:


            field_texts = xpath_text(f"//row[quotals_quota_id='{quota_id}']/{field}")


            langs = xpath_text(f"//row[quotals_quota_id='{quota_id}']/quotals_language")

            dict_element = {lang: txt for lang, txt in zip(langs, field_texts)}
            if dict_element:
                for target_language in target_languages:
                    target_lang_exist = bool(root.xpath(f"//row[quotals_quota_id='{quota_id}'][quotals_language='{target_language}']"))
                    if target_lang_exist is False:
                        dict_element[target_language] = ""

                dict_element["quotals_quota_id"] = quota_id
                dict_element["field"] = field
                dict_element["section"] = "quota_languagesettings"
                try:
                    validate_element(dict_element, dict_element["section"])
                except ValueError as e:
                    print(f"Validation error: {e}")
                new_order.append(dict_element)

    #group IDS
    gids= root.xpath("//groups/rows/row/gid/text()")
    group_order = root.xpath("//groups/rows/row/group_order/text()")
    sorted_gids = list(OrderedDict.fromkeys(x for _, x in sorted(zip(group_order, gids), key=lambda pair: int(pair[0]))))

    for gid in sorted_gids:
        langs = xpath_text(f"//groups/rows/row[gid='{gid}']/language")
        for field in  ["group_name", "description"]:

            field_texts = xpath_text(f"//groups/rows/row[gid='{gid}']/{field}")
            dict_element = {lang: txt for lang, txt in zip(langs, field_texts)}
            if dict_element:
                for target_language in target_languages:
                    target_lang_exist = bool(root.xpath(f"//groups/rows/row[language='{target_language}']"))
                    if target_lang_exist is False:
                        dict_element[target_language] = ""

                dict_element["gid"] = gid
                dict_element["field"] = field
                dict_element["section"] = "groups"
                try:
                    validate_element(dict_element, dict_element["section"])
                except ValueError as e:
                    print(f"Validation error: {e}")
                new_order.append(dict_element)

        #questions: IDS, titles, (actual) questions, helps, langs
        questions_base_path = f"//questions/rows/row[gid='{gid}']"
        qids = xpath_text(f"{questions_base_path}/qid")
        question_order = root.xpath(f"{questions_base_path}/question_order/text()")
        sorted_qids = list(OrderedDict.fromkeys(x for _, x in sorted(zip(question_order, qids), key=lambda pair: int(pair[0]))))


        for qid in sorted_qids:
            question_base_path = f"//questions/rows/row[qid='{qid}']"
            # titles = xpath_text(f"{question_base_path}/title")
            # questions = xpath_text(f"{question_base_path}/question")
            # helps = xpath_text(f"{question_base_path}/help")
            langs = xpath_text(f"{question_base_path}/language")

            for field in ["question", "help",]:
                field_texts = xpath_text(f"{question_base_path}/{field}")
                dict_element = {lang: txt for lang, txt in zip(langs, field_texts)}
                if dict_element:
                    for target_language in target_languages:
                        target_lang_exist = bool(root.xpath(f"{question_base_path}[language='{target_language}']"))
                        if target_lang_exist is False:
                            dict_element[target_language] = ""
                    dict_element["qid"] = qid
                    dict_element["gid"] = gid
                    dict_element["field"] = field
                    dict_element["section"] = "questions"
                    try:
                        validate_element(dict_element, dict_element["section"])
                    except ValueError as e:
                        print(f"Validation error: {e}")
                    new_order.append(dict_element)

            question_attributes_path = f"//question_attributes/rows/row[qid='{qid}' and language]"
            question_values = xpath_text(f"{question_attributes_path}/value")
            question_attributes = xpath_text(f"{question_attributes_path}/attribute")
            langs = xpath_text(f"{question_attributes_path}/language")
            for lang, value, attribute in zip(langs, question_values, question_attributes):
                dict_element = {lang: value }

                if dict_element:
                    for target_language in target_languages:
                        target_lang_exist = bool(root.xpath(f"//question_attributes/rows/row[qid='{qid}' and language='{target_language}']"))
                        if target_lang_exist is False:
                            dict_element[target_language] = ""
                    dict_element["qid"] = qid
                    dict_element["attribute"] = attribute
                    dict_element["field"] = "value"
                    dict_element["section"] = "question_attributes"
                    try:
                        validate_element(dict_element, dict_element["section"])
                    except ValueError as e:
                        print(f"Validation error: {e}")
                    new_order.append(dict_element)


            #subquestions
            subquestions_path = f"//subquestions/rows/row[parent_qid='{qid}']"#f"//subquestions/rows/row[qid={qid} and language]"
            subquestions_ids = xpath_text(f"{subquestions_path}/qid")
            if subquestions_ids: #s'il n'y a pas de sous question, inutile
                subquestions_order = xpath_text(f"{subquestions_path}/question_order")
                sorted_subquestions_ids = list(OrderedDict.fromkeys(x for _, x in sorted(zip(subquestions_order, subquestions_ids), key=lambda pair: int(pair[0]))))
                for subquestion_id in sorted_subquestions_ids:

                    subquestion_base_path = f"//subquestions/rows/row[qid='{subquestion_id}']"

                    langs = xpath_text(f"{subquestion_base_path}/language")
                    for field in ["question", "help",]:
                        field_texts = xpath_text(f"{subquestion_base_path}/{field}")
                        dict_element = {lang: txt for lang, txt in zip(langs, field_texts)}
                        if dict_element:
                            for target_language in target_languages:
                                target_lang_exist = bool(root.xpath(f"{subquestion_base_path}[language='{target_language}']"))
                                if target_lang_exist is False:
                                    dict_element[target_language] = ""
                            dict_element["qid"] = subquestion_id
                            dict_element["parent_qid"] = qid
                            dict_element["gid"] = gid
                            dict_element["field"] = field
                            dict_element["section"] = "subquestions"
                            try:
                                validate_element(dict_element, dict_element["section"])
                            except ValueError as e:
                                print(f"Validation error: {e}")
                            new_order.append(dict_element)

            #answers IDS
            answers_path = f"//answers/rows/row[qid='{qid}']"#f"//subquestions/rows/row[qid={qid} and language]"
            answers_ids = xpath_text(f"{answers_path}/code")

            if answers_ids: #s'il n'y a pas d'option de réponse, inutile

                answers_order = xpath_text(f"{answers_path}/sortorder")
                sorted_answers_ids = list(OrderedDict.fromkeys(x for _, x in sorted(zip(answers_order, answers_ids), key=lambda pair: int(pair[0]))))
                for answer_id in sorted_answers_ids:

                    answer_base_path = f"//answers/rows/row[qid='{qid}' and code='{answer_id}']"

                    langs = xpath_text(f"{answer_base_path}/language")
                    for field in ["answer"]:
                        field_texts = xpath_text(f"{answer_base_path}/{field}")
                        dict_element = {lang: txt for lang, txt in zip(langs, field_texts)}
                        if dict_element:
                            for target_language in target_languages:
                                target_lang_exist = bool(root.xpath(f"{answer_base_path}[language='{target_language}']"))
                                if target_lang_exist is False:
                                    dict_element[target_language] = ""
                            dict_element["qid"] = qid
                            dict_element["code"] = answer_id

                            dict_element["field"] = field
                            dict_element["section"] = "answers"
                            try:
                                validate_element(dict_element,
                                                 dict_element["section"],
                                                 identifier=f"{qid}-{answer_id}")
                            except ValueError as e:
                                print(f"Validation error: {e}")
                            new_order.append(dict_element)
    output_dict = {}
    for target_lang in target_languages:
        xliff = etree.Element("xliff", version="1.2", nsmap=NSMAP)
        file_elem = etree.SubElement(xliff, "file", attrib={
            "original": lss_file_path,
            "source-language": source_lang,
            "target-language": target_lang,
            "datatype": "xml"
        })
        body = etree.SubElement(file_elem, "body")

        for element in new_order:

            section = element["section"]
            field = element["field"]

            unique_id = [section, field]
            if section == "surveys_languagesettings":

                unique_id = "-".join(unique_id)


                trans_unit = etree.SubElement(body, "trans-unit", attrib={"id": unique_id})

                source = etree.SubElement(trans_unit, "source")
                source.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)
                html_fragments = html.fragments_fromstring(element[source_lang])
                for node in html_fragments:
                    if isinstance(node, str):
                        if source.text is None:
                            source.text = node
                        else:
                            source.text += node
                    else:
                        source.append(node)


                target = etree.SubElement(trans_unit, "target")

                target.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)
                if unique_id in target_id_to_keep or unique_id.startswith(tuple(target_group_id_to_keep)):

                    html_fragments = html.fragments_fromstring(element[target_lang])
                    for node in html_fragments:
                        if isinstance(node, str):
                            if target.text is None:
                                target.text = node
                            else:
                                target.text += node
                        else:
                            target.append(node)

            elif section == "quota_languagesettings":

                unique_id.append(element["quotals_quota_id"])
                unique_id = "-".join(unique_id)

                trans_unit = etree.SubElement(body, "trans-unit", attrib={"id": unique_id})
                source = etree.SubElement(trans_unit, "source")
                source.text = element[source_lang]
                source.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

                target = etree.SubElement(trans_unit, "target")
                if unique_id in target_id_to_keep or unique_id.startswith(tuple(target_group_id_to_keep)):
                    target.text = element[target_lang]
                target.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)

            elif section == "groups": #gid
                unique_id.append(element["gid"])
                unique_id = "-".join(unique_id)

                trans_unit = etree.SubElement(body, "trans-unit", attrib={"id": unique_id})
                source = etree.SubElement(trans_unit, "source")
                source.text = element[source_lang]
                source.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

                target = etree.SubElement(trans_unit, "target")
                if unique_id in target_id_to_keep  or unique_id.startswith(tuple(target_group_id_to_keep)):
                    target.text = element[target_lang]
                target.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)


            elif section == "questions": #gid-qid
                unique_id.extend([element["gid"],
                                             element["qid"],

                                             ])
                unique_id = "-".join(unique_id)
                trans_unit = etree.SubElement(body, "trans-unit", attrib={"id": unique_id})
                source = etree.SubElement(trans_unit, "source")
                source.text = element[source_lang]
                source.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

                target = etree.SubElement(trans_unit, "target")
                if unique_id in target_id_to_keep  or unique_id.startswith(tuple(target_group_id_to_keep)):
                    target.text = element[target_lang]
                target.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)



            elif section == "question_attributes": #parent_question_id-attribute
                unique_id.extend([#element["gid"],
                                             element["qid"],
                                             element["attribute"]
                                             ])
                unique_id = "-".join(unique_id)
                trans_unit = etree.SubElement(body, "trans-unit", attrib={"id": unique_id})
                source = etree.SubElement(trans_unit, "source")
                source.text = element[source_lang]

                source.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

                target = etree.SubElement(trans_unit, "target")
                if unique_id in target_id_to_keep or unique_id.startswith(tuple(target_group_id_to_keep)):
                    if target_lang in element:
                        target.text = element[target_lang]

                target.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)



            elif section == "subquestions": #gid-parent_id-subq_id
                unique_id.extend([element["gid"],
                                             element["parent_qid"],
                                             element["qid"],
                                             ])
                unique_id = "-".join(unique_id)
                trans_unit = etree.SubElement(body, "trans-unit", attrib={"id": unique_id})
                source = etree.SubElement(trans_unit, "source")
                source.text = element[source_lang]
                source.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

                target = etree.SubElement(trans_unit, "target")
                if unique_id in target_id_to_keep or unique_id.startswith(tuple(target_group_id_to_keep)):
                    target.text = element[target_lang]
                target.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)

            elif section == "answers": #gid-qid-code
                unique_id.extend([#element["gid"],
                                element["qid"],
                                element["code"],

                                             ])
                unique_id = "-".join(unique_id)
                trans_unit = etree.SubElement(body, "trans-unit", attrib={"id": unique_id})
                source = etree.SubElement(trans_unit, "source")
                source.text = element[source_lang]
                source.set("{http://www.w3.org/XML/1998/namespace}lang", source_lang)

                target = etree.SubElement(trans_unit, "target")
                if unique_id in target_id_to_keep or unique_id.startswith(tuple(target_group_id_to_keep)):
                    target.text = element[target_lang]
                target.set("{http://www.w3.org/XML/1998/namespace}lang", target_lang)

        output_xml = etree.tostring(xliff, pretty_print=False, encoding="utf-8",
                               xml_declaration=True,
                               method="xml")
        output_dict[target_lang] = output_xml
    return output_dict



def xliff_to_LSS(xliff_file_path, original_LSS_path):
    lss_parser = create_parser()
    lss_tree = etree.parse(original_LSS_path, parser=lss_parser)
    lss_root = lss_tree.getroot()

    xliff_tree = etree.parse(xliff_file_path)
    xliff_root = xliff_tree.getroot()
    for el in xliff_root.iter():
        el.tag = etree.QName(el.tag).localname
        for attr in list(el.attrib):
            if attr == "{http://www.w3.org/XML/1998/namespace}lang":
                continue
            if attr.startswith("{") or attr == "xmlns" or attr.startswith("xmlns:"): #TODO "{" is a bit dirty, find another solution
                del el.attrib[attr]
    for trans_unit in xliff_root.xpath("//trans-unit"):

        trans_id = trans_unit.get("id")

        section = trans_id.split("-")[0]
        target = trans_unit.find("target")
        source = trans_unit.find("source")

        if trans_id is not None and target is not None:
            inner = (target.text or "") + "".join(
                        etree.tostring(child, encoding="unicode")
                        for child in target
                    )

            if not inner.strip():
                continue  # skip if truly empty
            target_lang = target.get("{http://www.w3.org/XML/1998/namespace}lang")
            source_lang = source.get("{http://www.w3.org/XML/1998/namespace}lang")
            base_xpath = f".//{section}/rows/row[language='{target_lang}']"
            # source_base_xpath = f".//{section}/rows/row[language='{source_lang}']"
            field = trans_id.split("-")[1]
            if section == "surveys_languagesettings":
                #this section needs to be treated a bit differently from the others
                # print(f".//{section}/rows/row[surveyls_language='{target_lang}']")
                target_xml_block = lss_root.xpath(f".//{section}/rows/row[surveyls_language='{target_lang}']")[0]
                element = target_xml_block.find(field)
                # element.text = etree.CDATA(target.text)
                # for child in target:
                #     child.xpath(f'//*[namespace-uri()="{XLIF_NS}"]')
                # raw = etree.tostring(target, encoding="unicode")
                # # raw looks like: <target xmlns="...">...content...</target>
                # # We want only the inner content, which lxml gives us via:
                # inner = (target.text or "") + "".join(
                #     etree.tostring(child, encoding="unicode")
                #     for child in target
                # )
                # element.text = etree.CDATA(inner.strip()))
                element.text = etree.CDATA(inner.strip())


                # element.text = etree.CDATA(target.text)
            elif section == "quota_languagesettings":
                #same thing for quotas, a bit different
                quota_id = trans_id.split("-")[2]
                target_xml_block = lss_root.xpath(f".//{section}/rows/row[quotals_quota_id='{quota_id}' and quotals_language='{target_lang}']")[0]
                element = target_xml_block.find(field)
                element.text = etree.CDATA(target.text)

            else:

                if section == "groups":
                    gid = trans_id.split("-")[2]
                    #on va filtrer le xpath sur le gid (identidiant du groupe)
                    base_xpath += f"[gid={gid}]"


                elif section == "questions":
                    gid = trans_id.split("-")[2]
                    qid = trans_id.split("-")[3]
                    base_xpath += f"[gid='{gid}' and qid='{qid}']"
                elif section == "question_attributes":
                    qid = trans_id.split("-")[2]

                    attribute = trans_id.split("-")[3]
                    base_xpath += f"[qid='{qid}' and attribute='{attribute}']"



                elif section == "subquestions":
                    gid = trans_id.split("-")[2]
                    parent_qid = trans_id.split("-")[3]
                    qid = trans_id.split("-")[4]
                    base_xpath += f"[qid='{qid}' and gid='{gid}' and parent_qid='{parent_qid}']"
                elif section == "answers":
                    qid = trans_id.split("-")[2]
                    code = trans_id.split("-")[3]
                    base_xpath += f"[qid='{qid}' and code='{code}']"

                #TODO: check if base_xpath exists. If it does not, we
                #have to check if the parent xml block exists.
                #if it does not, we have to create all of it,
                #copying the source language one.
                elements = lss_root.xpath(base_xpath)

                if section != "question_attributes":
                    element =  elements[0].find(f"{field}" )

                else:

                    alt_xpath = base_xpath.replace(f"language='{target_lang}'",
                                                   f"language='{source_lang}'")

                    source_elements = lss_root.xpath(alt_xpath)
                    new_block = copy.deepcopy(source_elements[0])
                    for lang_tag in new_block.xpath("language"):
                        new_block.remove(lang_tag)
                    language_tag = etree.SubElement(new_block, "language")
                    language_tag.text = etree.CDATA(target_lang.strip())

                    lss_root.find(f".//{section}/rows").append(new_block)
                    element = new_block.find(field)

                element.text = etree.CDATA(target.text.strip())

    output_xml = etree.tostring(lss_root,
                           pretty_print=True,
                           encoding="utf-8",
                           xml_declaration=True)
    return output_xml
