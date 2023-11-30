class SwaggerChanges:
    def __init__(self, vOld, vNew):
        self.endpoints = 0
        self.new_params = 0
        self.param_changes = 0
        self.total_count = 0
        self.differences, self.total_changes, self.changed_paths = ({"old": {}, "new": {}} for _ in range(3))
        for key in ["old", "new"]:
            self.differences[key] = {
                "version": vOld if key == "old" else vNew, 
                "new_endpoints": {}, 
                "new_params": {}, 
                "param_changes": {}
            } 
        
        
    def append(self, version, type, path, value):
        current_position = self.differences[version][type]
        positions = path.split(".")
        key = positions[-1]
        for level in positions:
            if level != key:
                if level not in current_position:
                    current_position[level] = {}
                current_position = current_position[level]
        current_position[key] = value
        
        if type not in self.total_changes[version]:
            self.total_changes[version][type]=0
            self.changed_paths[version][type]=[]
        self.total_changes[version][type] += 1
        self.changed_paths[version][type].append(path)
        self.total_count += 1
           
            
        
    def get_totals(self, version=None, type=None, new_file="/tmp/swagger.json"):
        total_old = sum(self.total_changes['old'].values()) if sum(self.total_changes['old'].values()) > 0 else "No Changes"
        total_new = sum(self.total_changes['new'].values()) if sum(self.total_changes['new'].values()) > 0 else "No Changes"
        
        print_string = """
        Totals Differences: %s
        -----------------------------------------------------------------------------
        File Name: swagger.json (Currently on this CLI)
        File Version %s:
        Differences: %s
            {
                %s
            }
        -----------------------------------------------------------------------------        
        File Name: %s (Current on Ferry)
        File Version %s:
        Differences: %s
            %s
        """ % (self.total_count, 
               self.differences['old']['version'], 
               total_old,
               """
               """.join([f"""
                {" ".join([k.capitalize().replace("Param", "Parameter") for k in key.split("_")])}: {val}
                Items:[
                        %s
                    ]
                """ % ("""
                        """.join([endpoint.replace("paths.", "").replace(".", " -> ") for endpoint in self.changed_paths['old'][key]])) for key, val in self.total_changes['old'].items()]),
               new_file,
               self.differences['new']['version'],
               total_new,
               """{
                   %s
               }
               """ % ("    \n                  ".join([f"'{key}': {val}" for key, val in self.total_changes['new'].items()])) if total_new != "No Changes" else ""
        )
        print(print_string)
        return print_string, self.differences
        
    def compare_json(self, path, old_endpoints, new_endpoints):
        """
        Recursively compare two JSON objects and return the differences.
        """
        for key in old_endpoints.keys() | new_endpoints.keys():
            sub_path = f"{path}.{key}"
            if not self._log_new("new_endpoints", key, old_endpoints, new_endpoints, sub_path):
                # Endpoint exists in both dicts, step into the dictionary
                for mtype in ["get", "post", "put"]:
                    if mtype in old_endpoints[key]:
                        method = mtype
                if not method:
                    print("Not a listed type")
                    exit(1)
                    
                sub_path = f"{sub_path}.{method}"
                old_definition = old_endpoints[key].get(method, None)
                new_definition = new_endpoints[key].get(method, None)
                
                if not self._is_equal_or_nonexistant(sub_path, old_definition, new_definition):
                    d_path = f"{sub_path}.description"
                    if not self._is_equal_or_nonexistant(d_path, old_definition, new_definition):
                        if not self._log_new("new_params", "description", old_definition, new_definition, d_path):
                            if old_definition["description"] != new_definition["description"]:
                                self.append("old", "param_changes", d_path, {"CLI_value": old_definition["description"], "ferry_value": new_definition["description"]})
                                
                    old_params = {param["name"]: param for param in old_definition.get("parameters", [])}
                    new_params = {param["name"]: param for param in new_definition.get("parameters", [])}
                    
                    if not self._is_equal_or_nonexistant(f"{sub_path}.parameters", old_params, new_params):
                        for p in old_params.keys() or new_params.keys():
                            p_path = f"{sub_path}.parameters.{p}"
                            if not self._is_equal_or_nonexistant(p_path, old_params, new_params):
                                if not self._log_new("new_params", p, old_params, new_params, p_path):
                                    if old_params[p] != new_params[p]:
                                        modified = []
                                        for p_key in old_params[p].keys() | new_params[p].keys():
                                            if p_key not in old_params[p] or p_key not in new_params[p]:
                                                modified.append(p_key)
                                            elif old_params[p][p_key] != new_params[p][p_key]:
                                                modified.append(p_key)
                                        self.append("old", "param_changes", p_path, {
                                            
                                            "modified_fields": [{"field": field, "ferry_value":  new_params[p].get(field, "None"), "CLI_value": old_params[p].get(field, "None")} for field in modified]
                                            })
                                    
    def _log_new(self, t, key, d1, d2, path):
        if key in d1 and key not in d2:
            # We created the endpoint
            self.append("old", t, path, d1[key])
            return True
        elif key in d2 and key not in d1:
            # New endpoint exists in fetched swagger.json file
            self.append("new", t, path, d2[key])
            return True
        return False
    
    def _is_equal_or_nonexistant(self, path, old, new):
        if not old:
            print(f"{path} doesn't exist in the current swagger")
            return True
        if not new:
            print(f"{path} doesn't exist in the latest swagger")
            return True
        if old == new:
            return True
        return False


            
        
        
        
            
        