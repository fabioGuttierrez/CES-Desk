"""
Management command para popular dados iniciais do sistema.
Uso: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

CATEGORIES = [
    {
        'name': 'Admissão',
        'description': 'Integração de novos colaboradores, envio de documentos e cadastro',
        'icon': '👤',
        'sla_hours': 48,
        'order': 1,
        'auto_response': (
            'Olá! Recebemos sua solicitação de Admissão.\n\n'
            'Para dar continuidade, por favor envie os seguintes documentos:\n\n'
            '• RG / CNH (frente e verso)\n'
            '• CPF\n'
            '• Comprovante de endereço (últimos 3 meses)\n'
            '• Certidão de nascimento ou casamento\n'
            '• Carteira de Trabalho (CTPS)\n'
            '• PIS / NIS\n'
            '• Foto 3x4\n'
            '• Título de eleitor\n'
            '• Certificado de reservista (homens)\n'
            '• Dados bancários para depósito\n\n'
            'Nosso prazo de processamento é de até 2 dias úteis após o recebimento completo da documentação.\n\n'
            'Atenciosamente,\nEquipe DP'
        ),
    },
    {
        'name': 'Demissão',
        'description': 'Cálculo rescisório, homologação e documentos de desligamento',
        'icon': '📋',
        'sla_hours': 24,
        'order': 2,
        'auto_response': (
            'Olá! Recebemos sua solicitação de Demissão.\n\n'
            'Para calcularmos a rescisão, precisamos das seguintes informações:\n\n'
            '• Nome completo do colaborador\n'
            '• CPF\n'
            '• Data de admissão\n'
            '• Data de desligamento\n'
            '• Motivo do desligamento\n'
            '• Saldo de férias e banco de horas\n\n'
            'Entraremos em contato em breve.\n\nAtenciosamente,\nEquipe DP'
        ),
    },
    {
        'name': 'Folha de Pagamento',
        'description': 'Lançamentos, adicionais, descontos e fechamento de folha',
        'icon': '💰',
        'sla_hours': 24,
        'order': 3,
        'auto_response': (
            'Olá! Recebemos sua solicitação referente à Folha de Pagamento.\n\n'
            'Nossa equipe verificará as informações e entrará em contato.\n'
            'Lembre-se que o prazo de processamento depende do calendário de fechamento.\n\n'
            'Atenciosamente,\nEquipe DP'
        ),
    },
    {
        'name': 'Benefícios',
        'description': 'Vale transporte, vale alimentação, plano de saúde e outros benefícios',
        'icon': '🎁',
        'sla_hours': 48,
        'order': 4,
        'auto_response': '',
    },
    {
        'name': 'FGTS / INSS',
        'description': 'Divergências, guias, extratos e recolhimentos',
        'icon': '🏦',
        'sla_hours': 48,
        'order': 5,
        'auto_response': '',
    },
    {
        'name': 'eSocial',
        'description': 'Erros, eventos e obrigações do eSocial',
        'icon': '💻',
        'sla_hours': 24,
        'order': 6,
        'auto_response': '',
    },
    {
        'name': 'Férias',
        'description': 'Programação, adiantamento e aviso de férias',
        'icon': '🏖️',
        'sla_hours': 48,
        'order': 7,
        'auto_response': (
            'Olá! Recebemos sua solicitação de Férias.\n\n'
            'Por favor, informe:\n'
            '• Nome do colaborador\n'
            '• Período aquisitivo\n'
            '• Data de início das férias desejada\n'
            '• Quantidade de dias\n'
            '• Deseja adiantar parcela do 13°? (S/N)\n\n'
            'Atenciosamente,\nEquipe DP'
        ),
    },
    {
        'name': 'Afastamentos',
        'description': 'INSS, auxílio-doença, acidente de trabalho e outros afastamentos',
        'icon': '🏥',
        'sla_hours': 24,
        'order': 8,
        'auto_response': '',
    },
    {
        'name': 'Dúvidas Gerais',
        'description': 'Perguntas sobre CLT, políticas internas e procedimentos',
        'icon': '❓',
        'sla_hours': 72,
        'order': 9,
        'auto_response': (
            'Olá! Recebemos sua dúvida.\n\n'
            'Nossa equipe responderá em breve. Enquanto isso, você pode consultar nossa '
            'Base de Conhecimento que contém artigos sobre os principais temas do DP.\n\n'
            'Atenciosamente,\nEquipe DP'
        ),
    },
]


class Command(BaseCommand):
    help = 'Popula dados iniciais: categorias de tickets e superusuário admin'

    def handle(self, *args, **options):
        self._create_categories()
        self._create_superuser()
        self.stdout.write(self.style.SUCCESS('Dados iniciais criados com sucesso!'))

    def _create_categories(self):
        from apps.tickets.models import TicketCategory

        for cat_data in CATEGORIES:
            obj, created = TicketCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'sla_hours': cat_data['sla_hours'],
                    'order': cat_data['order'],
                    'auto_response': cat_data['auto_response'],
                },
            )
            status = 'Criada' if created else 'Já existia'
            self.stdout.write(f'  [{status}] Categoria: {obj.name}')

    def _create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@servicedesk-dp.com',
                password='admin123',
                role='admin',
            )
            self.stdout.write(self.style.WARNING(
                '  [Criado] Superusuário: admin / admin123 — TROQUE A SENHA!'
            ))
        else:
            self.stdout.write('  [Existe] Superusuário admin já existe.')
