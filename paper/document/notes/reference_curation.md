# Reference Curation for the IJIT Draft

This file is a working curation list for the paper
`Time-Budgeted Value-Maximizing Transit Itinerary Planning on GTFS Networks`.

Goal:
- keep the final bibliography around 50 references;
- center the review on GTFS/public-transit routing, tourist trip design,
  multi-objective optimization, and transit network optimization;
- avoid padding the list with weakly related LLM or unrelated optimization papers.

Interpretation of the `Action` column:
- `keep`: already in the local CSV and worth using.
- `add`: missing core/classic paper that should be added.
- `reserve`: optional backup if more references are needed later.
- `drop`: do not use in the main paper.

## Final Recommended Pool (50)

| ID | Action | Group | Title | Why it belongs |
| --- | --- | --- | --- | --- |
| 1 | keep | Transit routing | Round-Based Public Transit Routing | Core RAPTOR reference; method backbone. |
| 2 | add | Transit routing | Trip-Based Public Transit Routing | Direct benchmark family against RAPTOR-style methods. |
| 3 | keep | Transit routing | Scalable Algorithms for Bicriterion Trip-Based Transit Routing | Strong trip-based multi-criteria routing reference. |
| 4 | keep | Transit routing | Arc-Flags Meet Trip-Based Public Transit Routing | Speedup techniques for timetable routing. |
| 5 | keep | Transit routing | FLASH-TB: Integrating Arc-Flags and Trip-Based Public Transit Routing | Recent acceleration variant in the same family. |
| 6 | add | Transit routing | Intriguingly Simple and Fast Transit Routing | Canonical Connection Scan Algorithm paper. |
| 7 | keep | Transit routing | A schedule-based Public Transit Routing Algorithm for Finding K-shortest Paths Considering Transfer Penalties | Relevant schedule-based public-transit routing variant. |
| 8 | keep | Transit routing | Efficient Route Planning for Real-Time Demand-Responsive Transit | Useful real-time transit-routing comparison paper. |
| 9 | keep | Transit routing | Smart City Public Transportation Route Planning Based on Multi-objective Optimization: A Review | Review-level background for urban public transport routing. |
| 10 | keep | Transit routing | Real-time Approximate Routing for Smart Transit Systems | Practical real-time routing reference. |
| 11 | keep | Transit routing | Supporting public transit research in healthcare settings: testing a free, fast, and secure method for routing public transit | Applied GTFS-style routing use case. |
| 12 | add | Transit routing | Route Planning in Transportation Networks | Broad survey paper for route-planning context. |
| 13 | keep | TTDP / OP | A systematic literature review for the tourist trip design problem: extensions, solution techniques and future research directions | Strong recent TTDP review. |
| 14 | add | TTDP / OP | A survey on algorithmic approaches for solving tourist trip design problems | Classic TTDP survey. |
| 15 | keep | TTDP / OP | Solving the tourist trip planning problem with attraction patterns using meta-heuristic techniques | Direct TTDP solver comparison. |
| 16 | keep | TTDP / OP | A constraint programming approach for multi-objective tourist trip design problem with mandatory visits: A case study for Izmir Turkey | Multi-objective TTDP with real-case flavor. |
| 17 | keep | TTDP / OP | Recommendation of tourist itineraries with dependence on transport time | Strong fit to itinerary planning with transport-time dependence. |
| 18 | keep | TTDP / OP | Contextual analysis of solutions in a tourist trip design problem: A fuzzy logic-based approach | Context-aware TTDP extension. |
| 19 | keep | TTDP / OP | Optimized Travel Itineraries: Combining Mandatory Visits and Personalized Activities | Personalized itinerary design with constraints. |
| 20 | keep | TTDP / OP | Some Metaheuristics for Tourist Trip Design Problem | Baseline metaheuristics close to the paper's experiments. |
| 21 | keep | TTDP / OP | A simulated annealing-based recommender system for solving the tourist trip design problem | Direct SA-based TTDP reference. |
| 22 | keep | TTDP / OP | Solving the tourist trip design problem with time windows and variable profit using incremental local search | Direct local-search reference close to ILS/VNS discussion. |
| 23 | keep | TTDP / OP | A Critical Analysis of a Tourist Trip Design Problem with Time-Dependent Recommendation Factors and Waiting Times | Good for modeling-scope discussion. |
| 24 | keep | TTDP / OP | A new accessibility based team orienteering approach for urban tourism routes optimization (A Real Life Case) | Urban tourism routing with multi-objective flavor. |
| 25 | keep | TTDP / OP | The Green Tourist Trip Design Problem with Time Windows: A Model Application on a Urban Scale | Time-window and sustainability extension. |
| 26 | keep | TTDP / OP | An optimization approach for green tourist trip design | Green TTDP variant. |
| 27 | keep | TTDP / OP | Energy-constrained orienteering problem for green tourist trip design: Mathematical formulation and heuristic solution approaches | Recent OP-style tourism extension. |
| 28 | keep | TTDP / OP | A GRASP to solve the multi-constraints multi-modal team orienteering problem with time windows for groups with heterogeneous interests | Useful multi-modal and multi-constraint reference. |
| 29 | keep | TTDP / OP | A PERSONALIZED TOURIST TRIP DESIGN ALGORITHM FOR MOBILE TOURIST GUIDES | Early personalized TTDP reference. |
| 30 | keep | TTDP / OP | Orienteering Problem: A survey of recent variants, solution approaches and applications | Broad OP survey supporting the formulation section. |
| 31 | keep | TTDP / OP | Heuristic Search for the Orienteering Problem with Time-Varying Reward | Time-dependent OP variant. |
| 32 | keep | TTDP / OP | Adaptive Probabilistic Planning for the Uncertain and Dynamic Orienteering Problem | Uncertain/dynamic OP extension. |
| 33 | keep | TTDP / OP | A Reinforcement Learning Approach to the Orienteering Problem with Time Windows | Modern OP/TW variant; useful as a forward-looking comparator. |
| 34 | keep | TTDP / OP | Multi-objective Trip Planning with Solution Ranking Based on User Preference and Restaurant Selection | Scenario-style trip planning and ranking. |
| 35 | keep | TTDP / OP | A Modular Social Sensing System for Personalized Orienteering in the COVID-19 Era | Personalized orienteering reference. |
| 36 | keep | TTDP / OP | A novel user-centric happiness model for personalized tour recommendations | User-preference oriented supporting reference. |
| 37 | add | Optimization | A fast and elitist multiobjective genetic algorithm: NSGA-II | Mandatory for the NSGA-II baseline. |
| 38 | add | Optimization | Variable neighborhood search | Mandatory for the VNS baseline. |
| 39 | add | Optimization | Iterated Local Search: Framework and Applications | Mandatory for the ILS baseline. |
| 40 | add | Optimization | Optimization by Simulated Annealing | Mandatory for the SA baseline. |
| 41 | keep | Optimization | Optimizing Route Planning via the Weighted Sum Method and Multi-Criteria Decision-Making | Supports weighted-sum objective discussion. |
| 42 | keep | Optimization | A crossover-based multi-objective discrete particle swarm optimization model for solving multi-modal routing problems | Multi-objective routing support. |
| 43 | keep | Transit optimization | An artificial fish swarm optimization algorithm for the urban transit routing problem | Urban transit optimization comparator. |
| 44 | keep | Transit optimization | Trip route optimization based on bus transit using genetic algorithm with different crossover techniques: a case study | Bus-transit GA optimization example. |
| 45 | keep | Transit optimization | A demand based route generation algorithm for public transit network design | Strong network-design reference. |
| 46 | keep | Transit optimization | Solving urban transit route design problem using selection hyper-heuristics | Transit route design + heuristic search. |
| 47 | keep | Transit optimization | A Reinforcement Learning approach for bus network design and frequency setting optimisation | Modern network-design reference. |
| 48 | keep | Transit optimization | An Intelligent Heuristic Algorithm for a Multi-Objective Optimization Model of Urban Rail Transit Operation Plans | Multi-objective urban transit operations. |
| 49 | keep | Transit optimization | Optimization of Transit Route and Frequency for Integrated Urban-Rural Transit Network | Route/frequency optimization support. |
| 50 | keep | Transit optimization | Designing transit routes based on vehicle routing behavior determined through location-based services data | Data-driven transit route design. |

## High-Priority Additions with Verified Canonical Metadata

These are the most important missing papers to add even if the final list is shortened.

| Title | Key metadata |
| --- | --- |
| Trip-Based Public Transit Routing | Sascha Witt, ESA 2015, DOI: 10.1007/978-3-662-48350-3_85 |
| Intriguingly Simple and Fast Transit Routing | Julian Dibbelt, Thomas Pajor, Ben Strasser, Dorothea Wagner, 2013, DOI: 10.1007/978-3-642-38527-8_6 |
| Route Planning in Transportation Networks | Hannah Bast et al., chapter/survey, 2016, DOI: 10.1007/978-3-319-49487-6_2 |
| A fast and elitist multiobjective genetic algorithm: NSGA-II | Kalyanmoy Deb et al., 2002, DOI: 10.1109/4235.996017 |
| Variable neighborhood search | Nenad Mladenovic, Pierre Hansen, 1997, DOI: 10.1016/S0305-0548(97)00031-2 |
| Iterated Local Search: Framework and Applications | Helena R. Lourenco, Olivier C. Martin, Thomas Stutzle, 2003, DOI: 10.1007/0-306-48056-5_11 |
| Optimization by Simulated Annealing | S. Kirkpatrick, C. D. Gelatt Jr., M. P. Vecchi, 1983, DOI: 10.1126/science.220.4598.671 |
| A survey on algorithmic approaches for solving tourist trip design problems | Damianos Gavalas et al., 2014, DOI: 10.1007/s10732-014-9242-5 |

## Reserve List

Use only if the bibliography still needs to be padded after writing the related-work section.

| Action | Title | Note |
| --- | --- | --- |
| reserve | KomoTrip: a multi-day travel itinerary recommendation method based on the discrete komodo mlipir algorithm | Use only if you want a recent multi-day tourism recommender example. |
| reserve | Optimal routing and request selection for multiple service routes in a demand-adaptive transit system | More DRT than fixed-timetable transit. |
| reserve | Analyzing the benefits of an integrated mobility system using a matheuristic routing algorithm | Useful if the discussion expands to integrated mobility. |
| reserve | Collaborative optimization method for multiple feeder buses timetables for bridging rail transit | Better for feeder-schedule discussion than route planning. |
| reserve | Metro Route Optimization for Urban Public Transportation Using Q-Learning | Use only if you need more AI-based transit optimization references. |

## Drop List

These papers are too far from the current paper's scope, too weak, or both.

| Action | Title | Why to drop |
| --- | --- | --- |
| drop | Plugging Small Models in Large Language Models for POI Recommendation in Smart Tourism | LLM-based POI recommendation, not transit itinerary optimization. |
| drop | Recommendation as Instruction Following: A Large Language Model Empowered Recommendation Approach | General recommender-systems paper, not needed here. |
| drop | Large Language Model Enhanced Recommender Systems: Taxonomy, Trend, Application and Future | Off-topic for this paper. |
| drop | Large Language Models Augmented Rating Prediction in Recommender System | Off-topic for transit/TTDP routing. |
| drop | A survey on large language models for recommendation | Off-topic. |
| drop | How Can Recommender Systems Benefit from Large Language Models: A Survey | Off-topic. |
| drop | Recommender Systems in the Era of Large Language Models (LLMs) | Off-topic. |
| drop | Large Language Models are Zero-Shot Rankers for Recommender Systems | Off-topic. |
| drop | The application of large language models in recommendation systems | Off-topic. |
| drop | Large Language Models for Decision-Making Enhancement in Tourism Package Customization | Too far from GTFS routing. |
| drop | CTourLLM: enhancing LLMs with Chinese tourism knowledge | LLM tourism system, not relevant. |
| drop | Robust Planning with LLM-Modulo Framework: Case Study in Travel Planning | LLM planning, off the paper's method line. |
| drop | Quality Assurance for LLM-RAG Systems: Empirical Insights from Tourism Application Testing | Off-topic. |
| drop | Whose journey matters? Investigating identity biases in large language models (LLMs) for travel planning assistance | Interesting, but not for this methods paper. |
| drop | Unequal Opportunities: Examining the Bias in Geographical Recommendations by Large Language Models | Off-topic. |
| drop | Industrial applications of large language models | Off-topic. |
| drop | Integrated Sensing and Communications: Recent Advances and Ten Open Challenges | Completely unrelated. |
| drop | Electric Vehicle Routing with Public Charging Stations | Routing, but wrong domain. |
| drop | The Orienteering Problem with Drones | Wrong application setting. |
| drop | Round Trip Routing for Energy-Efficient Drone Delivery Based on a Public Transportation Network | Interesting but too far from the paper scope. |
| drop | Architectural Design and Implementation of a Psychological Testing Website Integrated with Large Language Models for... | Unrelated. |
| drop | Implementation of Round Robin Algorithm in Public Transportation Scheduling System at Pakupatan Terminal in Serang City | Too weak and not research-central. |
| drop | Artificial Intelligence-Based Demand Forecasting and Route Optimization Modeling for Public Transportation in Megacities | Too generic unless a very strong venue version is confirmed. |
| drop | Enhancing Public Transit System Through AI and IoT | Too generic. |
| drop | Survey Paper on Automated Tour Planner | Too weak compared with better TTDP surveys already available. |

## Recommended Writing Strategy

For the final paper, distribute the references roughly as follows:

- Related Work:
  - 8 to 10 public-transit routing papers
  - 10 to 12 TTDP / orienteering papers
  - 5 to 6 optimization-foundation papers
  - 4 to 6 transit network optimization papers
- Method / baselines:
  - explicitly cite RAPTOR, Trip-Based Routing, NSGA-II, VNS, ILS, and SA
- Discussion:
  - optionally cite 2 to 4 recent scenario or sustainability extensions

Practical next step:
- build the BibTeX from DOI exports for the 50 titles above;
- then reduce or expand by 3 to 5 papers after the Related Work section is drafted.
