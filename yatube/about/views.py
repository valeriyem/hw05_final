from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['just_title'] = 'Привет, я Валера'
        context['just_text'] = ' Моя страница на Github: valeriyem, ' \
                               'в данный момент у меня ' \
                               'не так много увлечений' \
                               'и программирование ' \
                               'стало одним из них, ' \
                               'люблю наблюдать за тем, ' \
                               'как код, состоящий из ' \
                               'букв и цифр оживает.'
        return context


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['just_title'] = 'Технологии'
        context['just_text'] = 'Я создал приложение, ' \
                               'где пользователи могут' \
                               'делитсья своими постами, ' \
                               'для этого я использовал' \
                               'основы ООП, создавал отдельные приложения, ' \
                               'в которых' \
                               'были свои модели, view-функции, ' \
                               'ссылащиемся на html коды. '
        return context
