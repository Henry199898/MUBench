import html
from os.path import join, basename, splitext
import re
from textwrap import wrap
from typing import Dict
from typing import List

from benchmark.data.misuse import Misuse
from benchmark.data.project_version import ProjectVersion
from benchmark.utils.io import safe_write
from benchmark.utils.java_utils import exec_util
from benchmark.utils.shell import CommandFailedError

REVIEW_RECEIVER_FILE = "review_submission_receiver.php"

ALL_VIOLATION_TYPES = [
    "missing/call",
    "missing/condition/null_check",
    "missing/condition/value_or_state",
    "missing/condition/threading",
    "missing/condition/environment",
    "missing/exception_handling",
    "superfluous/call",
    "superfluous/condition",
    "superfluous/exception_handling",
    "misplaced/call"
]


def generate_ex1(experiment: str, review_file: str, detector: str, compiles_path: str, version: ProjectVersion,
                 misuse: Misuse, potential_hits: List[Dict[str, str]]):
    review = """
        <h1>Review</h1>
        <table>
            <tr><td><b>Detector:</b></td><td>{}</td></tr>
            <tr><td><b>Target:</b></td><td>{}</td></tr>
            <tr><td><b>Misuse:</b></td><td>{}</td></tr>
        </table>
        <h2>Misuse Details</h2>
        <p>Details about the known misuse from the MUBench dataset.</p>
        <table class="fw">
            <tr><td class="vtop"><b>Description:</b></td><td>{}</td></tr>
            <tr><td class="vtop"><b>Fix Description:</b></td><td>{} (<a href="{}">see diff</a>)</td></tr>
            <tr><td class="vtop"><b>Violation Types:</b></td><td>{}</td></tr>
            <tr><td><b>In File:</b></td><td>{}</td></tr>
            <tr><td><b>In Method:</b></td><td>{}</td></tr>
            <tr><td class="vtop"><b>Code with Misuse:</b></td><td>{}</td></tr>
            <tr><td class="vtop"><b>Pattern Code:</b></td><td>{}</td></tr>
        </table>
        <h2>Potential Hits</h2>
        <p>Findings of the detector that identify an anomaly in the same file and method as the known misuse.
            Please reviews whether any of these findings actually correspond to the kown misuse.</p>
        <?php
            include_once "../../../../../review_utils.php";
            $review_file_name = "review_" . $_REQUEST["name"] . ".yml";
            if (file_exists($review_file_name)) {{
                $review = parse_review_yml(file_get_contents($review_file_name));
            }}
        ?>
        <form action="../../../../../{}" method="post" target="review_submission_target">
            {}
            <br/>
            <table>
                <tr><td><b>Reviewer Name:</b><br/>(lower case, no spaces)</td>
                    <td><input type="text" name="reviewer_name" pattern="[a-z]+" size="30" value="<?php echo $review["name"]; ?>" /></td></tr>
                <tr><td class="vtop"><b>Comment:</b></td>
                    <td><textarea name="reviewer_comment" cols="120" rows="8"><?php echo $review["comment"]; ?></textarea></td></tr>
            </table>
            <iframe name="review_submission_target" width="100%" height="100px" style="border-style:none"></iframe>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="review"/>
            <input type="submit" value="Save Review"/>
        </form>
        """.format(detector, version, misuse,
                   __multiline(misuse.description),
                   __multiline(misuse.fix.description),
                   misuse.fix.commit,
                   __list(misuse.characteristics),
                   misuse.location.file, html.escape(misuse.location.method),
                   __get_target_code(compiles_path, version, misuse.location.file, misuse.location.method),
                   __get_patterns_code(misuse),
                   REVIEW_RECEIVER_FILE,
                   __get_findings_table(potential_hits, misuse.characteristics),
                   experiment, detector, version.project_id, version.version_id, misuse.id)

    safe_write(__get_page(review), review_file, False)


def generate_ex2(experiment: str, review_file: str, detector: str, compiles_path: str, version: ProjectVersion,
                 misuse: Misuse, potential_hits: List[Dict[str, str]]):
    review = """
        <h1>Review</h1>
        <table>
            <tr><td><b>Detector:</b></td><td>{}</td></tr>
            <tr><td><b>Target:</b></td><td>{}</td></tr>
            <tr><td><b>Misuse:</b></td><td>{}</td></tr>
        </table>
        <h2>Misuse Details</h2>
        <p>Details about the known misuse from the MUBench dataset.</p>
        <table class="fw">
            <tr><td class="vtop"><b>Description:</b></td><td>{}</td></tr>
            <tr><td class="vtop"><b>Fix Description:</b></td><td>{} (<a href="{}">see diff</a>)</td></tr>
            <tr><td class="vtop"><b>Violation Types:</b></td><td>{}</td></tr>
            <tr><td><b>In File:</b></td><td>{}</td></tr>
            <tr><td><b>In Method:</b></td><td>{}</td></tr>
            <tr><td class="vtop"><b>Code with Misuse:</b></td><td>{}</td></tr>
        </table>
        <h2>Potential Hits</h2>
        <p>Findings of the detector that identify an anomaly in the same file and method as the known misuse.
            Please reviews whether any of these findings actually correspond to the kown misuse.</p>
        <?php
            include_once "../../../../../review_utils.php";
            $review_file_name = "review_" . $_REQUEST["name"] . ".yml";
            if (file_exists($review_file_name)) {{
                $review = parse_review_yml(file_get_contents($review_file_name));
            }}
        ?>
        <form action="../../../../../{}" method="post" target="review_submission_target">
            {}
            <br/>
            <table>
                <tr><td><b>Reviewer Name:</b><br/>(lower case, no spaces)</td>
                    <td><input type="text" name="reviewer_name" pattern="[a-z]+" size="30" value="<?php echo $review["name"]; ?>" /></td></tr>
                <tr><td class="vtop"><b>Comment:</b></td>
                    <td><textarea name="reviewer_comment" cols="120" rows="8"><?php echo $review["comment"]; ?></textarea></td></tr>
            </table>
            <iframe name="review_submission_target" width="100%" height="100px" style="border-style:none"></iframe>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="review"/>
            <input type="submit" value="Save Review"/>
        </form>
        """.format(detector, version, misuse,
                   __multiline(misuse.description),
                   __multiline(misuse.fix.description),
                   misuse.fix.commit,
                   __list(misuse.characteristics),
                   misuse.location.file, html.escape(misuse.location.method),
                   __get_target_code(compiles_path, version, misuse.location.file, misuse.location.method),
                   REVIEW_RECEIVER_FILE,
                   __get_findings_table(potential_hits, misuse.characteristics),
                   experiment, detector, version.project_id, version.version_id, misuse.id)

    safe_write(__get_page(review), review_file, False)


def generate_ex3(experiment: str, review_file: str, detector: str, compiles_path: str, version: ProjectVersion,
                 finding: Dict[str, str]):
    finding_name = splitext(basename(review_file))[0]
    review = """
        <h1>Review</h1>
        <table>
            <tr><td><b>Detector:</b></td><td>{}</td></tr>
            <tr><td><b>Target:</b></td><td>{}</td></tr>
        </table>
        <h2>Potential Misuse</h2>
        <p>Anomaly identified by the detector.
            Please review whether this anomaly corresponds to a misuse.</p>
        <?php
            include_once "../../../../review_utils.php";
            $review_file_name = "{}_" . $_REQUEST["name"] . ".yml";
            if (file_exists($review_file_name)) {{
                $review = parse_review_yml(file_get_contents($review_file_name));
            }}
        ?>
        <form action="../../../../{}" method="post" target="review_submission_target">
            <table class="fw">
                <tr><td><b>Finding:</b></td><td>{}</td></tr>
                <tr><td><b>In File:</b></td><td>{}</td></tr>
                <tr><td><b>In Method:</b></td><td>{}</td></tr>
                <tr><td class="vtop"><b>Code with Finding:</b></td><td>{}</td></tr>
                <tr><td class="vtop"><b>Metadata:</b></td><td>{}</td></tr>
                <tr><td><b>Reviewer Name:</b><br/>(lower case, no spaces)</td>
                    <td><input type="text" name="reviewer_name" pattern="[a-z]+" size="20" value="<?php echo $review["name"]; ?>" /></td></tr>
                <tr><td class="vtop"><b>Comment:</b></td>
                    <td><textarea name="reviewer_comment" cols="80" rows="5"><?php echo $review["comment"]; ?></textarea></td></tr>
            </table>
            <iframe name="review_submission_target" width="100%" height="100px" style="border-style:none"></iframe>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="hidden" name="review_name[]" value="{}"/>
            <input type="submit" value="Save Review" />
        </form>
        """.format(detector, version, finding_name, REVIEW_RECEIVER_FILE,
                   finding["id"], join(version.source_dir, finding["file"]), html.escape(finding["method"]),
                   __get_target_code(compiles_path, version, finding["file"], html.escape(finding["method"])),
                   __get_findings_table([finding], ALL_VIOLATION_TYPES),
                   experiment, detector, version.project_id, version.version_id, finding_name)

    safe_write(__get_page(review), review_file, False)


def __get_page(content: str):
    return """
        <html>
            <head>
                <style>
                    table.fw {{width:100%;}}
                    .vtop {{vertical-align:top}}
                    .prettyprint ol.linenums > li {{ list-style-type: decimal; }}
                </style>
                <script src="https://cdn.rawgit.com/google/code-prettify/master/loader/run_prettify.js?autoload=true&amp;skin=sunburst"></script>
            </head>
            <body>
            {}
            </body>
        </html>
    """.format(content)


def __get_target_code(compiles_path: str, version: ProjectVersion, file: str, method: str) -> str:
    version_compile = version.get_compile(compiles_path)
    misuse_file = join(version_compile.original_sources_path, file)

    code = ""
    try:
        output = exec_util("MethodExtractor", "\"{}\" \"{}\"".format(misuse_file, method)).strip("\n")

        # output comes as:
        #
        #   <first-line number>:<declaring type>:<code>
        #   ===
        #   <first-line number>:<declaring type>:<code>

        # if there's other preceding output, we need to strip it
        while output and not re.match("^[0-9]+:[^:\n]+:", output):
            output_lines = output.split("\n", 2)
            if len(output_lines) > 1:
                output = output_lines[1]
            else:
                output = ""

        if output:
            methods = output.split("\n===\n")
            for method in methods:
                info = method.split(":", 2)
                code += __get_snippet(int(info[0]) - 1,
                                      """class {} {{\n{}\n}}""".format(info[1], info[2].strip("\n")))
    except CommandFailedError as e:
        code += __get_snippet(1, html.escape(str(e)))

    return code


def __get_patterns_code(misuse: Misuse):
    snippets = []
    for pattern in misuse.patterns:
        with open(pattern.path, 'r') as pattern_file:
            pattern_code_lines = pattern_file.read().splitlines()
        pattern_code_lines = [line for line in pattern_code_lines if not __is_preamble_line(line)]
        snippets.append(__get_snippet(1, "\n".join(pattern_code_lines)))
    return "\n".join(snippets)


def __is_preamble_line(line: str):
    return line.startswith("import") or line.startswith("package") or not line


def __get_snippet(first_line: int, code: str):
    code = html.escape(code)
    return """<pre class="prettyprint linenums:{}"><code class="language-java">{}</code></pre>""".format(first_line,
                                                                                                         code)


def __get_findings_table(potential_hits: List[Dict[str, str]], violation_types: List[str]):
    keys = set()
    for potential_hit in potential_hits:
        keys.update(potential_hit.keys())
    keys.discard("file")
    keys.discard("method")
    keys.discard("id")
    keys = ["id"] + sorted(keys)

    def get_finding_row(finding):
        return __get_finding_row(keys, violation_types, finding)

    return """<table border="1" cellpadding="5">
        <tr><th>Hit</th><th>{}</th><th>Violation Type</tr>
        {}
        </table>
        """.format("</th><th>".join(keys), "\n".join(map(get_finding_row, potential_hits)))


def __get_finding_row(keys: List[str], violation_types: List[str], potential_hit: Dict[str, str]):
    values = map(lambda key: potential_hit.get(key, ""), keys)
    finding_id = potential_hit["id"]

    assessment_select = __select("assessment", finding_id, ["No", "Yes", "?"], False)
    violation_select = __select("violations", finding_id, violation_types, True)

    finding_row = """<tr>
            <td>{}</td>
            {}
            <td>{}</td>
        </tr>""".format(assessment_select,  "".join(map(__get_value_cell, values)), violation_select)
    return finding_row


def __get_value_cell(value):
    if type(value) is str:
        if not value.startswith("<img"):
            value = html.escape(value)
    elif type(value) is int:
        value = str(value)
    elif type(value) is list:
        value = __list(value)
    else:
        raise ValueError("unexpected value type '{}'".format(type(value)))
    return "<td>{}</td>".format(value)


def __multiline(text: str):
    return "<br/>".join(wrap(text, width=120))


def __list(l: List):
    if not list:
        return ""
    else:
        return """<ul>
                <li>{}</li>
            </ul>""".format("""</li>
                <li>""".join(map(html.escape, l)))


def __select(name: str, finding_id: str, l: List, multi_select: bool):
    select_name = "findings[{}][{}]".format(finding_id, name)

    if multi_select:
        attributes = """size="{}" multiple""".format(len(l))
        select_name += "[]"
    else:
        attributes = """size="1" """

    def select_option(option: str):
        return __select_option(name, finding_id, option, multi_select)

    return """<select name="{}" {}>{}</select>"""\
        .format(select_name, attributes, "".join(map(select_option, l)))


def __select_option(name: str, finding_id: str, option: str, multi_select: bool):
    check_variable = """$review["findings"][{}]["{}"]""".format(finding_id, name)
    if multi_select:
        check = """{} && in_array("{}", {})""".format(check_variable, option, check_variable)
    else:
        check = "{} === \"{}\"".format(check_variable, option)

    return """<option value="{}" <?php if({}) echo "selected"; ?>>{}</option>\n""".format(option, check, option)
