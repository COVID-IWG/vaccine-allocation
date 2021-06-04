
def run_visualization(state_code, district):
    if district:
        run_visualization_district(state_code, district)
    if state_code:
        run_visualization_state(state_code)
    else:
        run_visualization_natl()

def run_visualization_district(state_code, district):
    pass 

def run_visualization_state(state_code):
    pass

def run_visualization_natl():
    pass