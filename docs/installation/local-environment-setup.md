# Local Environment Setup (Development and Testing)

To execute the data processing pipelines of the simulator, defined as Apache Beam
pipelines, we use the Direct Runner. We define the pipelines using the Python SDK,
thus we need to set up a proper Python environment following the next steps:

1. Install Python 3.9 or greater
2. Create a virtual environment:

   `python3 -m venv .venv`
3. Activate the virtual environment:

   `source .venv/bin/activate`
4. Install required Python packages:

    `pip install -r requirements.txt`
5. Install custom `beam_mysql` Python package:

    `git clone https://gitlab.software.imdea.org/muse-lab/beam-mysql-connector.git`

    `cd beam-mysql-connector && pip install .`

**Important Note:** The [Direct Runner](https://beam.apache.org/documentation/runners/direct/)
must fit all user data in memory. Depending on the data we need to process, we
have to consider our machine specs.
