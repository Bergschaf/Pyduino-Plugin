############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################
import os
from typing import Optional

from pygls.lsp.methods import (TEXT_DOCUMENT_DID_OPEN, TEXT_DOCUMENT_DID_CHANGE)
from pygls.lsp.types import (CompletionList, CompletionParams, DidOpenTextDocumentParams,DidChangeTextDocumentParams)

from pygls.server import LanguageServer

from server.compiler.compiler import Compiler

print("Starting server...")

COUNT_DOWN_START_IN_SECONDS = 10
COUNT_DOWN_SLEEP_IN_SECONDS = 1

LAUNCH_JSON = """{
    "configurations": [
        {
            "name":"test",
            "type": "python",
            "request": "launch",
            "python": "${extensionInstallFolder:Bergschaf.pyduino-extension}/env/Scripts/python.exe",
            "program": "${extensionInstallFolder:Bergschaf.pyduino-extension}/main.py",
            "cwd": "${extensionInstallFolder:Bergschaf.pyduino-extension}",
            "args": [
                "${file}"
            ],
            "console": "internalConsole",
            "internalConsoleOptions": "openOnSessionStart"
        }
    ]   
}"""


class PyduinoLanguageServer(LanguageServer):
    runner = None
    CONFIGURATION_SECTION = 'pyduinoServer'

    def __init__(self, *args):
        super().__init__(*args)


pyduino_server = PyduinoLanguageServer('pygls-pyduino-example', 'v0.1')


def get_compiler(ls):
    text_doc = ls.workspace.get_document(list(ls.workspace.documents.keys())[0])
    source = text_doc.source
    return Compiler.get_compiler(source.split("\n"))


def _validate(ls, params):
    text_doc = ls.workspace.get_document(params.text_document.uri)

    diagnostics = _validate_pyduino(ls)

    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _validate_pyduino(source):
    """Validates json file."""
    errors = []
    compiler_pc, compiler_board = get_compiler(source)
    if compiler_pc is not None:
        compiler_pc.compile()
        errors += [error.get_Diagnostic() for error in compiler_pc.errors]

    if compiler_board is not None:
        compiler_board.compile()
        errors += [error.get_Diagnostic() for error in compiler_board.errors]

    print("errors", "\n".join([str(error) for error in compiler_pc.errors]))
    return errors


# @pyduino_server.feature(COMPLETION)  # comment  , CompletionOptions(trigger_characters=[',']))
def completions(ls, params: Optional[CompletionParams] = None) -> CompletionList:
    # not implemented yet
    return CompletionList(is_incomplete=False, items=[])


@pyduino_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    text_doc = ls.workspace.get_document(list(ls.workspace.documents.keys())[0])
    base_path = os.path.dirname(text_doc.path)

    if not os.path.exists(base_path + "\\\\.vscode"):
        os.mkdir(base_path + "\\\\.vscode")
    with open(base_path + "\\\\.vscode\\\\launch.json", "w") as f:
        f.write(LAUNCH_JSON)
    _validate(ls, params)


@pyduino_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)