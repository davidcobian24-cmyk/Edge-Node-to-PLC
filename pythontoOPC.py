import os
import time
from datetime import datetime
from opcua import Client
import mysql.connector

SERVER_URL     = os.getenv("OPC_SERVER_URL", "opc.tcp://Davids-MacBook-Pro-2.local:53530/OPCUA/SimulationServer")
NODE_IDS       = [f"ns=3;i={i}" for i in range(1001, 1008)]
NUM_SAMPLES    = 10
POLL_INTERVAL  = 1.0

MYSQL_HOST     = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "opcua_data")

def setup_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opcua_readings (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            sample           INT         NOT NULL,
            node_id          VARCHAR(32) NOT NULL,
            value            DOUBLE,
            status_code      VARCHAR(64),
            source_timestamp DATETIME(3),
            server_timestamp DATETIME(3),
            local_time       DATETIME(3) NOT NULL
        );
    """)

def insert_row(cur, row):
    cur.execute("""
        INSERT INTO opcua_readings
            (sample, node_id, value, status_code,
             source_timestamp, server_timestamp, local_time)
        VALUES
            (%(sample)s, %(node_id)s, %(value)s, %(status_code)s,
             %(source_timestamp)s, %(server_timestamp)s, %(local_time)s)
    """, row)

def print_last_ten(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT sample, node_id, value, status_code, local_time
        FROM opcua_readings
        ORDER BY id DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()

    print("\n" + "="*72)
    print("  Last 10 rows written to MySQL  —  opcua_data.opcua_readings")
    print("="*72)
    print(f"  {'sample':>6}  {'node_id':<14}  {'value':>16}  {'status':<10}  local_time")
    print(f"  {'─'*6}  {'─'*14}  {'─'*16}  {'─'*10}  {'─'*22}")
    for r in reversed(rows):
        sample, node_id, value, status, lt = r
        print(f"  {sample:>6}  {node_id:<14}  {str(value):>16}  {str(status):<10}  {lt}")
    print("="*72)

def main():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )
    cur = conn.cursor()
    setup_table(cur)
    conn.commit()
    print("MySQL connected — table ready.")

    opc = Client(SERVER_URL)
    opc.connect()
    print("OPC UA connected.\n")

    try:
        nodes = {nid: opc.get_node(nid) for nid in NODE_IDS}

        for sample in range(1, NUM_SAMPLES + 1):
            local_now = datetime.now()
            print(f"Sample {sample:02d}/{NUM_SAMPLES}  {local_now.strftime('%H:%M:%S')}")

            for nid, node in nodes.items():
                dv = node.get_data_value()
                row = {
                    "sample":           sample,
                    "node_id":          nid,
                    "value":            float(dv.Value.Value) if dv.Value.Value is not None else None,
                    "status_code":      str(dv.StatusCode),
                    "source_timestamp": dv.SourceTimestamp,
                    "server_timestamp": dv.ServerTimestamp,
                    "local_time":       local_now,
                }
                insert_row(cur, row)
                print(f"  {nid}  value={row['value']}")

            conn.commit()

            if sample < NUM_SAMPLES:
                time.sleep(POLL_INTERVAL)

        print_last_ten(conn)

    finally:
        cur.close()
        conn.close()
        opc.disconnect()
        print("\nDone — disconnected from OPC UA and MySQL.")

if __name__ == "__main__":
    main()
