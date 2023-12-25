def optimize_with_fixed_script(params, fixed_script_file):
    """
    Optimizes the design with the fixed script and writes down a new design file
    """
    optimized_design_file = None
    # TODO: run an scl session with the fixed script.

    params.design_file = optimized_design_file
    return params