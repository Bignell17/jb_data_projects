# Databricks notebook source
pip install pyvis

# COMMAND ----------

pip install networkx

# COMMAND ----------

import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

# COMMAND ----------

# Sample input format based on your data (simplified example)
relationships = {
    "EXBOI.PN*.ECT": [
        "NEX_MOS_INSTANCE",
        "NEX_MOS_SUB_LOC_DET (gas_month)",
        "NEX_MOS_REQUEST (loc_cd)",
        "NEX_MOS_SUB_LOC_DET (loc_cd)"
    ],
    "EXMLR.PN*.ECT": [
        "METER_SHPR_RLTNSP (shpr_cd)",
        "NEX_MTRSITE_LOC_RLTNSP (loc_cd)"
    ],
    # Add all your tables similarly...
}

# Create directed graph
G = nx.DiGraph()

# Add edges based on relationships
for table, associates in relationships.items():
    G.add_node(table)
    for assoc in associates:
        # Clean associated table name by removing columns in parentheses
        assoc_table = assoc.split()[0]
        G.add_node(assoc_table)
        # Add edge from table to associated table
        G.add_edge(table, assoc_table)

# Draw the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=0.5)  # Layout for nodes
nx.draw(G, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=8, arrowsize=15)
plt.title("Table Relationships DAG")
plt.show()


# COMMAND ----------

relationships = {
    "EXBOI.PN*.ECT": [
        "NEX_MOS_INSTANCE",
        "NEX_MOS_SUB_LOC_DET (gas_month)",
        "NEX_MOS_REQUEST (loc_cd)", "NEX_MOS_SUB_LOC_DET (loc_cd)",
        "NEX_MOS_SUB_LOC_DET (request_type)",
        "NEX_MOS_REQUEST (exercise_price)",
    ],
    "EXMLR.PN*.ECT": [
        "METER_SHPR_RLTNSP (shpr_cd)",
        "NEX_MTRSITE_LOC_RLTNSP (loc_cd)",
        "NEX_MTRSITE_LOC_RLTNSP (meter_site_id)",
        "METER_ACTV_STATS (meter_id)",
        "METER (site_id)", "METER_SHPR_RLTNSP (meter_id)",
        "NEX_MTRSITE_LOC_RLTNSP (rltnsp_eff_sdt)", "METER_ACTV_STATS (eff_st_date)",
        "METER_SHPR_RLTNSP (eff_st_date)",
        "NEX_MTRSITE_LOC_RLTNSP (rltnsp_eff_edt)", "METER_ACTV_STATS (eff_end_date)", "METER_SHPR_RLTNSP (eff_end_date)",
    ],
    "EXCAP.PN*.ECT": [
        "NEX_FLOW_SWAP_ENTLMT (gas_day)", "NEX_CONSTR_RESTR_DET (gas_day)",
        "NEX_ENTITLEMENT (loc_cd)", "NEX_FLOW_SWAP_ENTLMT (loc_cd)", "NEX_CONSTR_RESTR_DET (loc_cd)",
        "NEX_ENTITLEMENT (ba_cd)", "NEX_FLOW_SWAP_ENTLMT (ba_cd)",
        "NEX_ENTITLEMENT (entlmt_qty)",
    ],
    "EXOFR.PN.ECT": [],
    "NOMTN.PN*.ECT": [
        "NEX_MTRSITE_LOC_RLTNSP (loc_cd)",
    ],
    "SMD01.PN*.ACB": [
        "EC_IBEC_INCR_MVT (loc_cd)", "PRODUCT_QTY (loc_cd)",
        "EC_IBEC_TRANSFER_DETAILS",
        "EC_IBEC_INCR_MVT (ibec_incr_mvt_id)",
        "EC_SUBSTITUTION (transfer_qty)", "ibec_incr_mvt_id (transfer_qty)",
        "PRODUCT_QTY (available_qty)",
    ],
    "SMD01.PN*.ECR": [
        "EU_INTERRUPTBLE_CAP_REL (loc_cd)",
        "EU_INTERRUPTBLE_CAP_REL",
        "EU_INTERRUPTBLE_CAP_REL (uioli_int_cap)",
        "EU_INTERRUPTBLE_CAP_REL (descr_int_cap)",
        "EU_INTERRUPTBLE_CAP_REL (tot_int_cap_rel)",
    ],
    "MIPI3_PN*.MST": [
        "MEASRMT_PRE_METER_MEASRMT",
        "METER_ACTV_STATS (meter_id)", "METER (meter_id)", "METER_SHPR_RLTNSP (meter_id)", "MEASRMT_PRE_METER_MEASRMT (meter_id)",
        "METER (meter_name)",
        "MEASRMT_PRE_METER_MEASRMT (ltst_energy)",
        "MEASRMT_PRE_METER_MEASRMT (ltst_vol)",
        "MEASRMT_PRE_METER_MEASRMT (ltst_cv)",
        "METER (drctn_of_flow)",
    ],
    "SMD01.PN*.ONC": [
        "Location (location_cd)",
    ],
    "SMD01.PN*.SEE": [
        "BID (location_cd)", "EU_IP_TRADE_DET (location_cd)", "TRADE_DETAIL (location_cd)",
        "BID (ba_cd)",
        "MOS_DEFINITION",
        "BID (process_seqnum)", "BID (process_id)",  # 'OR' interpreted as separate entries
        "BID (entlmt_qty)",
        "EU_BID_TSO_DET (type_bundled)", "EU_IP_TRADE_DET (type_bundled)",
        "EU_IP_TRADE_DET (prisma_trade_id)", "TRADE_DETAIL (bid_id)",
    ],
    "SMD01.PN*.SNR": [
        "NOMTN_ACTIVITY (ser_id)", "BUSINESS_ASSTS (ba_name)",
        "NOMTN_NOMINATION (ba_cd)", "NOMTN_ACTIVITY (ba_cd)", "NOMTN_ACTIVITY (created_by)",
        "BA_BATYP_ASSNS (ba_cd)", "BUSINESS_ASSTS (ba_cd)",
        "NOMTN_ACTIVITY",
        "METER_LOCN_RLTNSP",
        "METER",
        "eu_ip_bal_mtr",
        "NOMTN_ACTIVITY (rate_schedule)",
        "NOMTN_NOMINATION (reqtd_energy)",
        "NOMTN_NOMINATION (schedd_energy)",
        "NOMTN_NOMINATION (activity_number)", "NOMTN_ACTIVITY",
    ],
    "SMD01.PN*.SUR": [
        "Process (mos_id)",
        "bid (mos_id)",
        "MOS_INSTANCE (mos_name)",
        "mos_sub_trans_detail (mos_id)",
        "eu_mos_view_qty (mos_id)",
        "Bid (loc_cd)",
        "location (loc_cd)",
        "mos_sub_trans_detail (location_cd)",
        "mos_qty (sold_qty)",
        "eu_mos_view_qty (type_bunded)",
        "eu_mos_view_qty (sold_cap_hr)",
        "mos_qty (qty_offered_hr)",
        "eu_mos_view_qty (off_cap_hr)",
        "eu_mos_view_qty (off_cap_hr)",
        "mos_qty (qty_unsold)",
    ],
    "SMD01.PN*.WBD": [
        "mos_instance (inst_type)",
        "Bid (mos_id)", "mos_instance",
        "Bid (location_cd)",
        "Bid (bid_id)",
        "Bid (bid_price)",
    ],
}


# COMMAND ----------

from pyvis.network import Network
import networkx as nx

G = nx.DiGraph()
edge_labels = {}

for table, associates in relationships.items():
    G.add_node(table)
    for assoc in associates:
        if "(" in assoc and ")" in assoc:
            assoc_table = assoc.split("(")[0].strip()
            column = assoc.split("(")[1].strip(")")
        else:
            assoc_table = assoc.strip()
            column = ""
        G.add_node(assoc_table)
        G.add_edge(table, assoc_table)
        if column:
            edge_labels[(table, assoc_table)] = column

net = Network(height='900px', width='100%', directed=True, notebook=False)

for node in G.nodes():
    net.add_node(node, label=node, title=node)

for u, v in G.edges():
    label = edge_labels.get((u, v), "")
    net.add_edge(u, v, label=label)  # <-- here, visible label on edges

net.barnes_hut(gravity=-30000, central_gravity=0.3, spring_length=150, spring_strength=0.01, damping=0.09)

net.show("table_relationships.html", notebook=False)


# COMMAND ----------

pip install --upgrade jinja2


# COMMAND ----------

from pyvis.network import Network
import networkx as nx

# Build graph and edge labels
G = nx.DiGraph()
edge_labels = {}

for table, associates in relationships.items():
    G.add_node(table)
    for assoc in associates:
        if "(" in assoc and ")" in assoc:
            assoc_table = assoc.split("(")[0].strip()
            column = assoc.split("(")[1].strip(")")
        else:
            assoc_table = assoc.strip()
            column = ""
        G.add_node(assoc_table)
        G.add_edge(table, assoc_table)
        if column:
            edge_labels[(table, assoc_table)] = column

# Create PyVis network - adjust height and width as needed
net = Network(height='900px', width='100%', directed=True, notebook=False)

# Add nodes and edges to PyVis network, with edge labels as titles
for node in G.nodes():
    net.add_node(node, label=node, title=node)

for u, v in G.edges():
    label = edge_labels.get((u, v), "")
    net.add_edge(u, v, title=label)

# Tweak physics to make layout less cluttered
net.barnes_hut(gravity=-30000, central_gravity=0.3, spring_length=150, spring_strength=0.01, damping=0.09)

# Optional: disable physics for a fixed layout or after initial run to stabilize
# net.toggle_physics(False)

# Save and open the interactive graph
net.show("table_relationships.html", notebook=)


# COMMAND ----------

from pyvis.network import Network
import networkx as nx

# Create a small example graph
G = nx.DiGraph()
G.add_edge("EXBOI.PN*.ECT", "NEX_MOS_INSTANCE")
G.add_edge("EXBOI.PN*.ECT", "NEX_MOS_SUB_LOC_DET")
edge_labels = {
    ("EXBOI.PN*.ECT", "NEX_MOS_INSTANCE"): "",
    ("EXBOI.PN*.ECT", "NEX_MOS_SUB_LOC_DET"): "gas_month"
}

net = Network(height='800px', width='100%', directed=True)

for node in G.nodes():
    net.add_node(node, label=node)

for u, v in G.edges():
    label = edge_labels.get((u, v), "")
    net.add_edge(u, v, title=label)

net.show("table_relationships.html")