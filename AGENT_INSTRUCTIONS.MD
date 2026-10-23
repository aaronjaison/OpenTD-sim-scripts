# Your Goal: Create OpenTD scripts that speed up simulation

## Rules
1. Always write in Python
2. Always create expansive testing using Pytest for any code written, separated into other files. Always maintain 100% code coverage in this testing
3. Follow the file format given, and make the code as readable and concise as possible. Leave comments explaining each block of code, and make use of well-named helper functions to break the code up into very small bits. If files become too long (150+ lines of code), create a new folder in place of that file and populate that folder with subfiles containing the code. For example, if /app/example.py becomes too long, create a folder in /app called /example, it's directory name being /app/example, and within the folder example populate files, such as example_one.py, example_two.py, etc, which break up the code from example.py. If you do create these subfolders, update the format names in the format and instructions section below to reflect that it's no longer just one python file, while keeping descriptions the same and adding individual descriptions for each of the python files within the subfolder.
4. Prioritize efficiency as much as possible, optimizing so all functions are O(n^2) or less
5. All new code should be added to a separate worktree for me to inspect and then pull request from

## Format and instructions
- /frontend - folder where all the graphics are created and used using the TKinter module. 
- /frontend/connections.py - file where functions that interacts with backend code are written. 
- /frontend/graphics.py - file where the functions creating the sprites are called.
- /frontend/interface.py - file where the interface is created. It calls functions from graphics.py to create the interface and relays the user's interactions to connections.py, which then does the processing necessary.
- /backend - folder where the bulk of the processing/work with OpenTD happens.
- /backend/con_interpreter.py - file that talks with /frontend/connections, updating connections (which then updates interface) on what internal processes are happening while also calling functions with main_processes
- backend/main_processes.py - file that handles all the main_processes, calls and keeps track of what happens in open_td_api.py, config.api, and results_interp.py.
- /backend/open_td_api.py - file that makes most of the API calls with open_td
- /backend/config.py - file that has functions that keep track of changes to simulation, such as physics boundary conditions, different files, different heat sources, etc., and is used by main_processes.py, in coordination with open_td_api.py, to run the trial.
- results_interp.py - file that logs the results in individual markdown files, including time, the name of the file used, and results (including graphs and raw numbers), as well as a csv file with just the numbers. Each result should be organized by folders within /output with time and name of the file used (as well as the number of times a trial has been run with said file) as the name of each of these subfolders within output. Each of these subfolders should have, as mentioned, a markdown file and a csv file.

## Other specifications
- within the interface, one should be able to upload their .SLDPRT and .SLDASM files and be able to configure the equations and numbers used in the physics simulations


## Prototype supporting modules
- /app.py - launches the Tkinter workbench.
- /frontend/layout.py - creates scrollable panels for smaller displays.
- /frontend/opentd_panel.py - presents prepared-case controls and queues OpenTD status updates.
- /backend/equations.py - parses and evaluates bounded arithmetic heat-input equations.
- /backend/solver.py - integrates the lumped thermal preview with RK4.
- /backend/plotting.py - generates SVG temperature plots from trial samples.
- /backend/opentd_trials.py - runs isolated copies of prepared Thermal Desktop cases and extracts a node temperature.
- /backend/results_interp.py - implements the results_interp.py responsibility described above.
- /tests - separate Pytest files covering all application modules, including real Tk widgets and vendor API contracts.
- /backend/opentd.runtimeconfig.json - selects the Windows Desktop .NET 8 framework for optional coreclr use.

The preview records SolidWorks source references but does not parse/mesh CAD geometry.
The OpenTD path requires a prepared DWG. Its case controls physical properties independently of preview inputs.

- /backend/toolchain.py - initializes installed Visual Studio x64 build tools for SINDA in this process only.

- /backend/reuse.py - matches saved reports to configurations and input fingerprints, loads results, and supports forced reruns.
- /frontend/test_queue.py - maintains FIFO test snapshots, visible status, waiting-test removal and selected-test reruns.

- /backend/node_catalog.py - reads unique available thermal node IDs from an isolated drawing copy without solving.
- /frontend/node_picker.py - displays the result-node dropdown and queues discovery, discarding results for a changed drawing.

- /backend/node_results.py - validates all-node histories and exports individual temperatures plus unweighted mean/minimum/maximum histories.

- /backend/sim_settings.py - validates prepared-model simulation inputs and applies required named case overrides.
- /frontend/sim_form.py - compact opt-in simulation settings with SI labels and help.
- /frontend/tooltips.py - reusable hover and keyboard-focus explanations.
- /DWG_PREPARATION.md - model-author checklist, named parameters, units, bindings and acceptance checks.

The current application presents one prepared-DWG workflow: file, case, simulation settings, result selection and test queue. The standalone preview is retained only as a backend utility, not as a separate UI tab.

- /backend/case_catalog.py - discovers existing case names and groups in an isolated drawing copy.
- /frontend/case_picker.py - selects exact cases/groups and rejects stale drawing results.
