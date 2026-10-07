import json

def parse_cube_to_json(cube_file_path):
    """
    .cube uzantılı LUT dosyasını okuyup JavaScript/WebGL veya 
    FFmpeg'in bellek üzerinde işleyebileceği bir JSON matrisine dönüştürür.
    """
    lut_data = {
        "title": "",
        "size": 0,
        "domain_min": [0.0, 0.0, 0.0],
        "domain_max": [1.0, 1.0, 1.0],
        "data": []
    }
    
    with open(cube_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if line.startswith('TITLE'):
            lut_data["title"] = line.split('"')[1] if '"' in line else line.split()[1]
        elif line.startswith('LUT_3D_SIZE'):
            lut_data["size"] = int(line.split()[1])
        elif line.startswith('DOMAIN_MIN'):
            lut_data["domain_min"] = [float(x) for x in line.split()[1:]]
        elif line.startswith('DOMAIN_MAX'):
            lut_data["domain_max"] = [float(x) for x in line.split()[1:]]
        else:
            parts = line.split()
            if len(parts) == 3:
                try:
                    lut_data["data"].append([float(parts[0]), float(parts[1]), float(parts[2])])
                except ValueError:
                    pass
                    
    return lut_data
