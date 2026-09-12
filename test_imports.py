from src.apps.masters.models import Master, MasterStatus
from src.apps.coordinator.models import Coordinateur
from src.apps.administrator.models import Administrateur
from src.apps.documents.models import RequiredDocument
from src.apps.scoring.models import ScoreFormula, ScoreCriterion

print('✓ All imports successful')
print(f'✓ Master: {Master._meta.app_label}.{Master.__name__}')
print(f'✓ Coordinateur: {Coordinateur._meta.app_label}.{Coordinateur.__name__}')
print(f'✓ Administrateur: {Administrateur._meta.app_label}.{Administrateur.__name__}')
print(f'✓ RequiredDocument: {RequiredDocument._meta.app_label}.{RequiredDocument.__name__}')
print(f'✓ ScoreFormula: {ScoreFormula._meta.app_label}.{ScoreFormula.__name__}')
print(f'✓ ScoreCriterion: {ScoreCriterion._meta.app_label}.{ScoreCriterion.__name__}')

# Verify relationships
master = Master.objects.first()
if master:
    print(f'\n✓ Sample Master: {master.nom}')
    print(f'  - Coordinateur: {master.coordinateur.nom if master.coordinateur else "None"}')
    print(f'  - Administrateur: {master.administrateur.nom if master.administrateur else "None"}')
