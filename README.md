# Ghost-Network-India
# 👻 Ghost Network India

### Interactive Network Simulation, Routing & Failure Analysis

<p align="center">
  <strong>Explore. Connect. Simulate. Analyze.</strong>
</p>

<p align="center">
  An interactive, India-focused network simulation platform for exploring network topology, communication paths, link failures, and rerouting behaviour through geographic visualizations and simulation dashboards.
</p>

<p align="center">
  <a href="YOUR_STREAMLIT_APP_URL">🚀 Live Demo</a> ·
  <a href="https://github.com/Saloni15apr/Ghost-Network-India">💻 GitHub Repository</a>
</p>

---

## 🌐 About the Project

**Ghost Network India** is an interactive network simulation application that demonstrates how communication networks can be represented, visualized, and analyzed using graph-based modelling.

The platform uses a geographic view of Indian cities to make network connectivity easier to understand. Users can explore network nodes and communication links, investigate source-to-destination paths, and observe how simulated failures affect network connections and routing.

By combining graph theory, network modelling, geographic visualization, and interactive dashboards, Ghost Network India provides a practical way to explore fundamental concepts in computer networks.

The project focuses on making network behaviour more visual, interactive, and understandable rather than presenting connectivity as an abstract collection of nodes and edges.

## 🎯 Project Objectives

- Represent a communication network using graph-based models.
- Visualize network nodes and connections across Indian cities.
- Explore communication paths between selected source and destination nodes.
- Understand routing and hop-count concepts through interactive simulations.
- Investigate the effect of simulated network failures on connectivity.
- Visualize network information and simulation indicators through dashboards.
- Provide an interactive environment for learning and experimenting with computer networking concepts.

## ✨ Key Features

### 🗺️ 1. Geographic Network Visualization

Explore a geographic representation of the simulated network across Indian cities. The map helps users understand the spatial distribution of nodes and visualize relationships between connected locations.

### 🔗 2. Network Topology Visualization

View the network as interconnected nodes and links. The graph-based representation helps illustrate how network structure determines connectivity between different points.

### 🧭 3. Source-to-Destination Path Analysis

Select source and destination nodes to examine the communication path between them. The displayed route helps explain intermediate nodes and the number of hops required to reach the destination.

### ⚡ 4. Network Failure Simulation

Explore simulated network disruptions and examine how they affect connections and communication paths. This feature helps demonstrate the consequences of link failures within a modelled network.

### 🔄 5. Routing & Rerouting Behaviour

Investigate how communication paths may change when a connection becomes unavailable. The simulation illustrates the role of alternative paths in maintaining connectivity when suitable routes exist.

### 📊 6. Interactive Network Dashboard

Inspect the network information and simulation indicators presented by the application. Visual summaries help users understand network structure, routing behaviour, and changes across simulation scenarios.

### 🧪 7. Interactive Experimentation

Explore different network scenarios through the available application controls. Users can investigate network behaviour and compare outcomes under different supported configurations.

## 🏗️ How It Works

Ghost Network India follows a simulation-oriented workflow:

1. **Network Representation:** Model the network as nodes and communication links.
2. **Geographic Visualization:** Display the network using a map-based interface.
3. **Path Selection:** Choose source and destination nodes to examine a communication route.
4. **Routing Analysis:** Inspect the path and related routing information.
5. **Failure Simulation:** Introduce a supported simulated disruption.
6. **Result Visualization:** Examine the resulting network state and displayed indicators.

### System Workflow

```text
        Network Configuration
                 |
                 v
         Graph Construction
                 |
                 v
      Geographic Visualization
                 |
                 v
       Source-Destination Path
                 |
                 v
        Failure Simulation
                 |
                 v
       Routing & Path Analysis
                 |
                 v
        Dashboard Visualization
```

## 🧠 Technical Concepts

| Concept | Description |
|---|---|
| Graph Theory | Represents a network through nodes and edges |
| Network Topology | Describes the structure and arrangement of network connections |
| Graph Traversal & Path Finding | Supports exploration of routes through a graph |
| Source & Destination | Defines the starting and ending points of communication |
| Hop Count | Represents the number of links traversed along a path |
| Link Failure | Models the unavailability of a communication connection |
| Rerouting | Examines alternative communication paths when available |
| Geographic Visualization | Places network information within a map-based interface |
| Network Simulation | Models network behaviour under specified conditions |
| Data Visualization | Presents network information through maps, charts, and dashboards |

*The exact algorithms used for path finding, routing, and failure handling should be documented according to the implementation in the source code.*

## 🛠️ Technology Stack

| Technology | Role |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application and user interface |
| NetworkX | Graph construction and network analysis |
| Folium | Geographic map visualization |
| streamlit-folium | Embedding interactive Folium maps in Streamlit |
| Pandas | Structured data handling |
| Plotly | Interactive charts and data visualization |

## 🏛️ Project Architecture

The application separates the user interface from the network simulation logic.

- **Application Layer:** Handles the interactive interface and user inputs.
- **Network Engine:** Supports graph construction and network-related operations.
- **Data Layer:** Stores or loads the datasets and supporting geographic information required by the application.
- **Visualization Layer:** Presents maps, network paths, and dashboard indicators.

This structure helps organize the project into understandable components and provides a foundation for future development.

## 📂 Repository Structure

```text
Ghost-Network-India/
│
├── app.py
├── network_engine.py
├── data/
├── requirements.txt
├── DATA_PROVENANCE.md
└── README.md
```

**File overview**

- `app.py` — Main Streamlit application and user interface.
- `network_engine.py` — Network modelling and simulation logic.
- `data/` — Supporting datasets and project resources.
- `requirements.txt` — Python package dependencies.
- `DATA_PROVENANCE.md` — Dataset sources and provenance documentation.
- `README.md` — Project documentation and setup instructions.

*This is a high-level structure; the repository may contain additional files and subdirectories.*

## 🚀 Getting Started

Run the project locally by following the steps below.

### Prerequisites

- Python installed on your system.
- Git installed on your system.
- pip for installing Python packages.

### 1. Clone the repository

```bash
git clone https://github.com/Saloni15apr/Ghost-Network-India.git
```

### 2. Navigate to the project directory

```bash
cd Ghost-Network-India
```

### 3. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install the dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Run the application

```powershell
python -m streamlit run app.py
```

The application will start locally, usually at:

`http://localhost:8501`

## ☁️ Live Deployment

Ghost Network India is deployed using **Streamlit Community Cloud**.

Access the hosted application here:

**[Launch Ghost Network India](YOUR_STREAMLIT_APP_URL)**

The deployed version allows users to explore the application through a web browser without setting up the project locally.

## 🔍 Example Exploration Scenarios

Users can explore questions such as:

- How are nodes and communication links represented in a network?
- What path connects a selected source to a destination?
- How many hops are required to traverse a communication path?
- What happens when a link in a selected path becomes unavailable?
- Can an alternative path be found after a simulated failure?
- How does network topology influence the availability of communication paths?
- How can maps and dashboards make network behaviour easier to understand?

These scenarios connect theoretical computer networking concepts with practical, visual experimentation.

## 🔬 Scope & Limitations

Ghost Network India is a **simulation and visualization project**, not a live telecommunications monitoring platform.

- Network failures and other incident scenarios are simulated.
- Geographic placement of nodes does not necessarily represent the actual physical infrastructure or routing of Indian telecom operators.
- Displayed performance indicators depend on the simulation logic and should not automatically be interpreted as real-world telecom measurements.
- The application does not directly control or monitor live telecommunications infrastructure.
- Routing and recovery outcomes depend on the network model, its configuration, and the algorithms implemented.
- The application does not claim to implement a separate, comprehensive network resilience analysis module.

These limitations define the scope of the project and help ensure that simulation results are interpreted appropriately.

## 🔮 Future Enhancements

Potential directions for further development include:

- Configurable random network generation and topology comparison.
- Support for additional routing algorithms.
- Comparative analysis of alternative routing strategies.
- Quantitative connectivity and network resilience metrics.
- Recovery-time analysis across repeated failure scenarios.
- Improved network performance analytics.
- Integration of appropriately sourced real-world network datasets.
- Advanced failure prediction and adaptive routing experiments.

These are proposed extensions, not claims about features already implemented.

## 🎓 Learning Outcomes

The project provides practical experience with:

- Applying graph theory to network modelling.
- Working with graph-based data structures.
- Exploring routing and path-finding concepts.
- Simulating network connectivity changes.
- Building interactive applications with Streamlit.
- Integrating geographic maps into data-driven interfaces.
- Presenting simulation outputs through visual dashboards.
- Organizing a Python project for deployment and public access.

## 👩‍💻 Author

**Saloni Ghutukade**  
Computer Engineering  
Vidyalankar Institute of Technology, Mumbai, India

GitHub: [@Saloni15apr](https://github.com/Saloni15apr)

## 🤝 Contributions & Feedback

Suggestions, bug reports, and ideas for improving the project are welcome.

If you would like to propose an enhancement, open an issue describing the proposed change and its intended purpose.

## 📄 License

A license has not yet been specified for this project. Add an appropriate `LICENSE` file to clarify the terms under which others may use, modify, or distribute the code.

---

<p align="center">
  <strong>Ghost Network India</strong>
  <br>
  Making network topology, routing, and failure behaviour easier to explore.
</p>
