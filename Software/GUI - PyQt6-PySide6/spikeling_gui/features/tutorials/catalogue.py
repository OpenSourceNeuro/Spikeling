"""Phase 2A: declarative, versioned Spikeling tutorial catalogue.

No scientific computations or live GUI mutations belong in this file.
Each step clearly distinguishes software evidence from manual confirmation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialStep:
    id: str
    title: str
    instruction: str
    target: str | None = None
    completion: str = "manual"
    hint: str = ""
    panel: str | None = None        # Navigation button (not an experimental control).
    prompt: str = ""               # Optional prediction / observation / interpretation.
    response_kind: str = ""        # predict | observe | explain
    require_response: bool = False
    confirmation: str = ""         # Explicit self-report, e.g. physical knob action.


@dataclass(frozen=True)
class Tutorial:
    id: str
    title: str
    module: str
    description: str
    duration_minutes: int
    requires_hardware: bool
    page: str
    steps: tuple[TutorialStep, ...]


TUTORIALS = (
    Tutorial(
        id="NI-04", title="Current injection and action potentials", module="Neuron Interface",
        description=("Conduct a complete current-clamp investigation on the physical board: "
                     "establish a baseline, predict responses, explore subthreshold voltage "
                     "changes and spiking, save a recording, and explain the evidence."),
        duration_minutes=18, requires_hardware=True,
        page="page_Spikeling_NeuronInterface",
        steps=(
            TutorialStep(
                "NI-04-01", "Connect the physical Spikeling",
                "Connect the board by USB. Choose its serial port and select Connect. "
                "A checked button alone is not sufficient: the board must report an active connection.",
                "Spikeling_ConnectButton", "board_connected",
                "Check that the USB cable carries data and no other application is using the serial port."),
            TutorialStep(
                "NI-04-02", "Identify membrane potential (Vm)",
                "Make the membrane-potential trace visible. Observe how Vm changes over time. "
                "This is the voltage of the Izhikevich-based model, not a measurement from a living cell.",
                "Spikeling_VmCheckbox", "vm_visible",
                "If Vm is hidden, tick the Vm trace checkbox in the recording display."),
            TutorialStep(
                "NI-04-03", "Prepare a physical current-clamp experiment",
                "Open Neuron Parameters and select Current Clamp (CC), not Voltage Clamp (VC). "
                "Disable the GUI patch-clamp override to return control to the physical knob. "
                "Then centre that knob to give approximately zero injected current. "
                "The app checks the displayed GUI mode and override, not a firmware acknowledgement "
                "or the physical knob's position.",
                "PatchClampMode_toggleButton", "cc_ready",
                "In CC the physical knob injects current. In VC it commands a voltage. "
                "With the GUI patch-clamp toggle ON, the knob is overridden.",
                panel="Spikeling_NeuronParameter_pushButton",
                confirmation="I selected CC, disabled the GUI override and centred the physical knob."),
            TutorialStep(
                "NI-04-04", "Describe the baseline",
                "Allow the trace to settle with the physical knob centred. Do not change "
                "the stimulus, pharmacology or synaptic controls during this baseline observation.",
                "Spikeling_VmCheckbox", "manual",
                "An approximately stable voltage is useful here; exact values depend on the chosen model and inputs.",
                prompt="What does the baseline Vm look like? Is the neuron firing already?",
                response_kind="observe", require_response=True),
            TutorialStep(
                "NI-04-05", "Predict hyperpolarisation",
                "Before moving the knob, predict what should happen when you inject negative current.",
                "Spikeling_VmCheckbox", "manual",
                "Think about the change in membrane voltage relative to the baseline, rather than memorising a number.",
                prompt="Predict the direction of Vm change and whether firing should become more or less likely.",
                response_kind="predict", require_response=True),
            TutorialStep(
                "NI-04-06", "Test negative current injection",
                "Gently turn the physical patch-clamp knob anticlockwise. Observe Vm. "
                "Then return it to the centre. The tutorial does not detect knob movement: "
                "describe the voltage response you actually saw.",
                "Spikeling_VmCheckbox", "manual",
                "If nothing changes, check that CC remains selected, the GUI override is OFF, "
                "and no protocol is holding the patch command.",
                prompt="What happened to Vm compared with your prediction?",
                response_kind="observe", require_response=True,
                confirmation="I moved the physical knob and then returned it to the centre."),
            TutorialStep(
                "NI-04-07", "Predict depolarisation and threshold",
                "Before increasing current, predict how Vm and spike firing might change "
                "as you inject progressively more positive current.",
                "Spikeling_VmCheckbox", "manual",
                "The response can depend on the selected Izhikevich model and other enabled inputs.",
                prompt="What will happen below threshold? What new behaviour do you expect above threshold?",
                response_kind="predict", require_response=True),
            TutorialStep(
                "NI-04-08", "Find spike initiation",
                "Turn the physical patch-clamp knob clockwise in small increments. "
                "Watch for depolarisation followed by full spikes. You may press Check "
                "once the streamed Vm contains a spike. If the graph shows spikes but "
                "the detector misses them, record your observation and confirm it manually.",
                "Spikeling_VmCheckbox", "spike_seen",
                "A detected spike verifies an event in the stream, not that a particular "
                "physical action caused it. Check for stimulus, synaptic or noise inputs.",
                prompt="Describe the transition from subthreshold responses to spikes.",
                response_kind="observe", require_response=True),
            TutorialStep(
                "NI-04-09", "Record and save the experiment",
                "Choose a new, descriptive file name. Start recording; capture several "
                "seconds of Vm while changing current. Stop recording and confirm that "
                "the CSV has been saved. The tutorial never starts or stops recording itself.",
                "Spikeling_DataRecording_Record_pushButton", "recording_saved",
                "Do not change CC/VC mode while recording. If the GUI displays Retry save, "
                "resolve the save problem before proceeding."),
            TutorialStep(
                "NI-04-10", "Interpret and repeat independently",
                "Return the physical knob to its centre. Explain which observations "
                "support your conclusion about injected current and excitability. "
                "Then, without using earlier step-by-step instructions, repeat one "
                "subthreshold and one spiking condition. This is an independent challenge, "
                "not an automatically scored experiment.",
                "Spikeling_VmCheckbox", "manual",
                "Distinguish the observed Vm response from the model-based explanation. "
                "A biological neuron may behave differently.",
                prompt="What evidence supports the relationship between injected current, Vm and firing? "
                       "Name one confounding variable and one model limitation.",
                response_kind="explain", require_response=True,
                confirmation="I repeated the observations independently and returned the knob to centre."),
        ),
    ),
    Tutorial(
        id="EM-01", title="Your first emulator experiment", module="Neuron Emulator",
        description=("Run a hardware-free experiment, change stimulus strength "
                     "and explain the resulting neuron activity."),
        duration_minutes=10, requires_hardware=False,
        page="page_Spikeling_NeuronEmulator",
        steps=(
            TutorialStep("EM-01-01", "Start the emulator",
                "Open the Neuron Emulator and start it. No Spikeling board is required.",
                "Emulator_Connect_pushButton", "emulator_running"),
            TutorialStep("EM-01-02", "Observe the membrane trace",
                "Find the Vm trace and note its baseline and any spontaneous spikes.",
                "Emulator_VmCheckbox"),
            TutorialStep("EM-01-03", "Find stimulus controls",
                "Open Stimulus Parameters and locate the strength and frequency controls.",
                "Emulator_StimulusParameter_pushButton"),
            TutorialStep("EM-01-04", "Make a prediction",
                "Predict how increasing a depolarising stimulus might change "
                "membrane potential and firing. The outcome depends on neuron mode.",
                "Emulator_StimStr_slider", panel="Emulator_StimulusParameter_pushButton",
                prompt="What qualitative change do you expect if depolarising stimulus strength increases?",
                response_kind="predict", require_response=True),
            TutorialStep("EM-01-05", "Run the test",
                "Enable an appropriate stimulus route and vary stimulus strength "
                "gradually. Keep other parameters constant and observe the result.",
                "Emulator_StimStr_slider", panel="Emulator_StimulusParameter_pushButton",
                prompt="What did you observe? Did the response support the prediction?",
                response_kind="observe", require_response=True),
            TutorialStep("EM-01-06", "Record and interpret",
                "Record a short run, then stop recording. Compare what you saw "
                "with your prediction and describe one model limitation.",
                "Emulator_DataRecording_Record_pushButton",
                prompt="Which part of this experiment is a model assumption rather than direct biological evidence?",
                response_kind="explain", require_response=True),
        ),
    ),
    Tutorial(
        id="DA-01", title="Explore your first recording", module="Neuron Data Analysis",
        description=("Load a Spikeling CSV, examine its channels, run spike "
                     "detection and consider measurement quality."),
        duration_minutes=12, requires_hardware=False,
        page="page_Spikeling_DataAnalysis",
        steps=(
            TutorialStep("DA-01-01", "Load a recording",
                "Use Load Data to open a Spikeling CSV recording. A synthetic example "
                "is bundled at Data/Tutorials/tutorial_CC_spikes.csv, or you can "
                "load a recording made with the board or Emulator.",
                "Spikeling_DataAnalysis_LoadData_pushButton", "recording_loaded",
                "The importer expects the Spikeling recording columns. "
                "It will reject missing required columns or an invalid time axis."),
            TutorialStep("DA-01-02", "Identify the signals",
                "Examine time, Vm, stimulus, total input current and, where "
                "available, synaptic channels. Note their different units.",
                "DataAnalysis_voltagePlot",
                prompt="Which trace represents Vm, and which traces represent input or stimulus?",
                response_kind="observe", require_response=True),
            TutorialStep("DA-01-03", "Choose a spike threshold",
                "Inspect the voltage trace and choose a spike-detection threshold "
                "that avoids counting subthreshold fluctuations as spikes.",
                "Spikeling_DataAnalysis_Spike_lineEdit"),
            TutorialStep("DA-01-04", "Measure spikes",
                "Run spike detection. Examine the detected events and consider "
                "whether they match the trace rather than trusting the count alone.",
                "Spikeling_DataAnalysis_Spike_Display_pushButton"),
            TutorialStep("DA-01-05", "Export and interpret",
                "Export your results or graph. What makes the measurements "
                "reproducible, and which sources of error remain?",
                "Spikeling_DataAnalysis_SaveImage_pushButton",
                prompt="Name one measurement choice and one source of uncertainty.",
                response_kind="explain", require_response=True),
        ),
    ),
)


def get_tutorial(identifier: str) -> Tutorial | None:
    return next((tutorial for tutorial in TUTORIALS if tutorial.id == identifier), None)


def validate_catalogue(tutorials: tuple[Tutorial, ...] = TUTORIALS) -> None:
    seen: set[str] = set()
    step_ids: set[str] = set()
    kinds = {"manual", "board_connected", "emulator_running", "recording_loaded",
             "vm_visible", "cc_ready", "spike_seen", "recording_saved"}
    response_kinds = {"", "predict", "observe", "explain"}
    for tutorial in tutorials:
        if not tutorial.id or tutorial.id in seen:
            raise ValueError(f"Duplicate/empty tutorial ID: {tutorial.id!r}")
        seen.add(tutorial.id)
        if not tutorial.steps or not tutorial.page:
            raise ValueError(f"Incomplete tutorial: {tutorial.id}")
        for step in tutorial.steps:
            if not step.id or step.id in step_ids:
                raise ValueError(f"Duplicate/empty tutorial step: {step.id!r}")
            if step.completion not in kinds:
                raise ValueError(f"Unknown completion type: {step.completion}")
            if step.response_kind not in response_kinds:
                raise ValueError(f"Unknown response type: {step.response_kind}")
            if step.require_response and not step.prompt:
                raise ValueError(f"Required response has no prompt: {step.id}")
            step_ids.add(step.id)


validate_catalogue()
