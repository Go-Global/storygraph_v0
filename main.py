from visualization import visualize
from models import *

if __name__ == '__main__':
    # Test graphdb models instantiation
    stef = Source('0', 'stef', 'person')
    main_code = Document('1', 'main.py', 'python-file')
    models_code = Document('2', 'models.py', 'python-file')
    # meta_stef = Entity('3')
    # code = Action('4')
    # meta_code = Entity('5')

    # Add edges
    coded1 = Authored(stef, main_code)
    coded2 = Authored(stef, models_code)

    # Test visualization
    visualize([stef, main_code, models_code], [coded1, coded2], title='TestGraph')
    


    pass