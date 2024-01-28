import pandas as pd
from ortools.linear_solver import pywraplp

# Read in data
df = pd.read_csv('data/draftstars.csv')
df = df.groupby('Name').head(1).reset_index(drop=True) # How to add this constraint ???
df.columns = [col.lower().replace(' ', '_') for col in df.columns]

# Create solver
solver = pywraplp.Solver.CreateSolver('CBC')

# Object to store optimisation results/indicies
player_ix = {k: solver.BoolVar('x_' + str(v)) for (k, v) in zip(df.index, df.index)}


# Total Player constraint
def player_count_constraint(solver):
    ct = solver.Constraint(9, 9, 'total_players')
    
    for x in player_ix:
        ct.SetCoefficient(player_ix[x], 1)
        
    return solver


# Player Position constraint
def position_constraint(solver):

    df['idx_ls'] = [[el] for el in df.index]
    pos_dict = df.groupby('position')['idx_ls'].agg('sum')
    pos_dict = dict(zip(list(pos_dict.index), list(pos_dict.values)))
    
    for pos in pos_dict:
        pos_count = 1 if pos == 'C' else 2
        ct = solver.Constraint(pos_count, pos_count, 'player_pos_' + pos)
        
        for ix in pos_dict[pos]:
            ct.SetCoefficient(player_ix[ix], 1)
            
    return solver


# Total Salary constriant
def salary_constraint(solver):
    ct = solver.Constraint(0, 100000, 'total_salary')
    
    for ix in player_ix:
        ct.SetCoefficient(player_ix[ix], int(df.iloc[ix]['salary']))
        
    return solver


# Combine all constraints
def add_constraints(solver):
    solver = player_count_constraint(solver)
    solver = position_constraint(solver)
    solver = salary_constraint(solver)
    return solver


# Objective function
def set_obj_function(solver, player_ix):
    objective = solver.Objective()
    
    for ix in player_ix:
        objective.SetCoefficient(player_ix[ix], df.iloc[ix]['form'])
        
    objective.SetMaximization()
    solver.Solve()
    
    return solver, player_ix, objective

# Execute code
solver = add_constraints(solver)
solver, player_ix, objective = set_obj_function(solver, player_ix)
df_team = df.iloc[[bool(int(el.solution_value())) for el in player_ix.values()]]
df_team = df_team[['name', 'position', 'team', 'salary', 'form', 'playing_status']].sort_values('salary', ascending=False)

print(f'''
    Generated team total PER: {round(df_team['form'].sum(), 2)}. \n 
    Total Team's salary:  ${round(df_team['salary'].sum(), 2)} 
''')

print(df_team)