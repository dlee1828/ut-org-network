import networkx as nx
import numpy as np

student_features = {
    'type':{'dtype': str, 'values':['student']},
    'year': {
        'dtype':int,

        # 1, 2, 3, 4, 5
        # Freshman, Sophmore, Junior, Senior, Grad Student
        'values':np.arange(5) + 1,
        'p': np.array([10 - i for i in range(5)])
    },
    'major': {
        'dtype':str,
        'values': ['STEM', 'Arts', 'Pre-Med', 'Other'],
        'p': np.array([10, 1, 2, 5])
    },
    'commitment_limit': {
        'dtype':int,
        'values': [15],
    }

}
    
org_features = {
    'type':{'dtype': str, 'values':['org']},
    'hour_req':{
        'dtype':int,
        'values':np.arange(12) + 1
    },
    'topic':{
        'dtype':str,
        'values': ['STEM', 'Arts', 'Pre-Med', 'Entertainment', 'Other'],
        'p': np.array([10, 2, 0, 8, 4])
    }

}

def augment_student(graph, students: dict or list, student_features=student_features):
    for feature in student_features.keys():
        feature_dict = student_features[feature]
        values = {}
        if type(students) == dict:
            students = list(students.keys())

        for s in students:
            p = None
            if feature_dict.get('p', None) is not None:
                p = feature_dict['p'] / feature_dict['p'].sum()
            values[s] = feature_dict['dtype'](np.random.choice(feature_dict['values'], p=p))

        nx.set_node_attributes(graph, values, feature)

def augment_org(graph, orgs: dict or list, org_features=org_features):
    augment_student(graph, orgs, student_features=org_features)

def synthesize_student(__studentname__=[1], student_features=student_features):
    student = {}
    for feature_name, feature_dict in student_features.items():
        p = None
        if feature_dict.get('p', None) is not None:
            p = feature_dict['p'] / feature_dict['p'].sum()
        student[feature_name] = feature_dict['dtype'](np.random.choice(feature_dict['values'], p=p))

    student['name'] = f'student_{__studentname__[0]}'
    student['id'] = __studentname__[0]
    __studentname__[0] += 1

    return (student['name'], student)

def synthesize_students(N, student_features=student_features):
    return [synthesize_student(student_features=student_features) for _ in range(N)]

def synthesize_org(__orgname__=[1], org_features=org_features):
    org = {}
    for feature_name, feature_dict in org_features.items():
        p = None
        if feature_dict.get('p', None) is not None:
            p = feature_dict['p'] / feature_dict['p'].sum()
        org[feature_name] = feature_dict['dtype'](np.random.choice(feature_dict['values'], p=p))

    org['name'] = f'org_{__orgname__[0]}'
    org['id'] = __orgname__[0]
    __orgname__[0] += 1

    return (org['name'], org)

def synthesize_orgs(N, org_features=org_features):
    return [synthesize_org(org_features=org_features) for _ in range(N)]

def synthesize_graph(N_students = 300, N_orgs = 15, student_features=student_features, org_features=org_features):
    G = nx.Graph()
    students = synthesize_students(N_students, student_features)
    orgs = synthesize_orgs(N_orgs, org_features)
    G.add_nodes_from(students)
    G.add_nodes_from(orgs)

    # attach students to orgs
    l1, l2, l3 = 0.5, 10, -0.1

    for student in students:
        hours_committed = 0
        s = student[1]
        sid = student[0]
        while hours_committed < s['commitment_limit']:
            orgs_can_join = [o for o in orgs if o[0] not in G[sid]]
            if len(orgs_can_join) == 0:
                break

            org_ids = [o[0] for o in orgs_can_join]

            # Calculate probability for each org
            degree = np.array([G.degree[o] for o in org_ids]) # Bigger orgs
            majors = np.array([G.nodes[o]['topic'] == s['major'] for o in org_ids], dtype='int')
            hours = np.array([G.nodes[o]['hour_req'] for o in org_ids])

            p = degree * l1 + majors * l2 + hours * l3        # Calc p metric
            q = p - p.min() + 0.00001                         # Set to positive and prevent NaN
            k = q / q.sum()                                   # Normalize
            
            org = np.random.choice(org_ids, p=k)
            G.add_edge(sid, org)

            hours_committed += [o[1]['hour_req'] for o in orgs_can_join if o[0] == org][0] # This line sucks - find a better way with numpy

            if np.random.random() < 0.1 * hours_committed:
                # Student stops signing up for things even if they haven't reached their absolute limit bc some have personal lives
                break

    return G