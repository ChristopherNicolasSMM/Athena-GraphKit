"""Portuguese and English strings for the account interface."""

ENGLISH = {
    'Entrar': 'Sign in',
    'Crie sua conta': 'Create your account',
    'Defina sua senha': 'Set your password',
    'Recuperar senha': 'Recover your password',
    'Definir nova senha': 'Set a new password',
    'Enviar link de cadastro': 'Send sign-up link',
    'Criar conta': 'Create account',
    'Enviar link': 'Send link',
    'Salvar senha': 'Save password',
    'Confirme seu e-mail para definir sua senha.': 'Confirm your email address to set your password.',
    'Informe o e-mail da sua conta para receber um link de recuperação.': 'Enter your account email to receive a reset link.',
    'E-mail': 'Email',
    'Senha': 'Password',
    'Esqueci minha senha': 'Forgot password?',
    'Use pelo menos 12 caracteres.': 'Use at least 12 characters.',
    'Confirmar senha': 'Confirm password',
    'Primeiro acesso?': 'New here?',
    'Solicitar novo link': 'Request a new link',
    'Voltar ao login': 'Back to sign in',
    'Idioma': 'Language',
    'Sessão do formulário inválida. Recarregue a página.': 'This form session has expired. Reload the page.',
    'Muitas tentativas. Aguarde e tente novamente.': 'Too many attempts. Please wait and try again.',
    'E-mail ou senha inválidos.': 'Invalid email or password.',
    'Informe um e-mail válido.': 'Enter a valid email address.',
    'Se o endereço puder ser cadastrado, você receberá um link para definir sua senha.':
        'If this email address can be registered, you will receive a link to set your password.',
    'Link inválido ou expirado. Solicite um novo cadastro.': 'This link is invalid or expired. Request a new sign-up link.',
    'As senhas digitadas são diferentes.': 'The passwords do not match.',
    'Use uma senha entre 12 e 256 caracteres.': 'Use a password between 12 and 256 characters.',
    'Se o e-mail estiver cadastrado, você receberá um link de recuperação.':
        'If this email address is registered, you will receive a password reset link.',
    'Link inválido ou expirado.': 'This link is invalid or expired.',
    'Senha atualizada. Entre com a nova senha.': 'Password updated. Sign in with your new password.',
}


def translate(message, language):
    return ENGLISH.get(message, message) if language == 'en' else message
