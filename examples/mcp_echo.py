import json
import sys


def main():
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            continue
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "manifest":
            result = {
                "name": "mcp_echo",
                "tools": [
                    {
                        "name": "echo",
                        "description": "Devuelve los parametros recibidos tal cual.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string", "description": "Mensaje a devolver"}
                            },
                            "required": ["message"]
                        }
                    }
                ],
            }
        elif method == "echo":
            result = {"echo": params}
        else:
            result = {"error": f"Metodo '{method}' no soportado"}

        response = {"jsonrpc": "2.0", "id": req_id, "result": result}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main() 