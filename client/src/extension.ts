/* -------------------------------------------------------------------------
 * Original work Copyright (c) Microsoft Corporation. All rights reserved.
 * Original work licensed under the MIT License.
 * See ThirdPartyNotices.txt in the project root for license information.
 * All modifications Copyright (c) Open Law Library. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License")
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http: // www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ----------------------------------------------------------------------- */
"use strict";

import * as net from "net";
import * as path from "path";
import { ExtensionContext, ExtensionMode, workspace, window, commands } from "vscode";
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
} from "vscode-languageclient/node";
import * as fs from "fs";
import { exec } from "child_process";

let client: LanguageClient;

function getClientOptions(): LanguageClientOptions {
    return {
        documentSelector: [
            { scheme: "file", language: "pyduino" },
            { scheme: "untitled", language: "pyduino" },
        ],
        outputChannelName: "[pygls] PyduinoLanguageServer",
        synchronize: {
            // Notify the server about file changes to '.clientrc files contain in the workspace
            fileEvents: workspace.createFileSystemWatcher("**/.clientrc"),
        },
    };
}

function startLangServerTCP(addr: number): LanguageClient {
    const serverOptions: ServerOptions = () => {
        return new Promise((resolve /*, reject */) => {
            const clientSocket = new net.Socket();
            clientSocket.connect(addr, "127.0.0.1", () => {
                resolve({
                    reader: clientSocket,
                    writer: clientSocket,
                });
            });
        });
    };

    return new LanguageClient(
        `tcp lang server (port ${addr})`,
        serverOptions,
        getClientOptions()
    );
}

function startLangServer(
    command: string,
    args: string[],
    cwd: string
): LanguageClient {
    const serverOptions: ServerOptions = {
        args,
        command,
        options: { cwd },
    };

    return new LanguageClient(command, serverOptions, getClientOptions());
}

export function activate(context: ExtensionContext): void {
    if (context.extensionMode === ExtensionMode.Development) {
        // Development - Run the server manually
        client = startLangServerTCP(2087);
        console.log("Development mode");
        context.subscriptions.push(client.start());
    }
        
    else {

    const cwd = path.join(__dirname, "..", "..");
    const pythonPath = "env/Scripts/python.exe"

    exec("where python", (error, stdout, stderr) => {
        if (error) {
            console.log(`error: ${error.message}`);
            return;
        }
        if (stderr) {
            console.log(`stderr: ${stderr}`);
        }
        console.log(`stdout: ${stdout}`);
        const interpreter = stdout.split("\n")[0];
        // remove the python.exe from the path
        const cfg = "home = " + interpreter.substring(0, interpreter.length - 12) + "\ninclude-system-site-packages = false";
        fs.writeFileSync(path.join(cwd, "env/pyvenv.cfg"), cfg);
        client = startLangServer(pythonPath, ["-m", "server"], cwd);
        context.subscriptions.push(client.start());

    });}



}

export function deactivate(): Thenable<void> {
    return client ? client.stop() : Promise.resolve();
}
