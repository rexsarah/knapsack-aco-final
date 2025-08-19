#include "problem.hpp"

#include <fstream>
#include <sstream>
#include <cctype>
#include <algorithm>
#include <stdexcept>

// ---------- helpers internos (arquivo .cpp) ----------

static bool is_comment_line(const std::string& s) {
    if (s.empty()) return true;
    size_t i = 0;
    while (i < s.size() && std::isspace((unsigned char)s[i])) ++i;
    if (i >= s.size()) return true;
    char c = s[i];
    // Linhas iniciando com #, %, c, C, p, P são consideradas comentário/meta
    return (c=='#' || c=='%' || c=='c' || c=='C' || c=='p' || c=='P');
}

// Scanner robusto: varre caractere a caractere e extrai inteiros
static std::vector<long long> read_all_numbers(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    std::vector<long long> nums;
    if (!in) return nums;

    std::string tok;
    tok.reserve(32);

    auto flush_tok = [&]() {
        // tem pelo menos um dígito?
        bool has_digit = false;
        for (char ch : tok) if (std::isdigit((unsigned char)ch)) { has_digit = true; break; }
        if (!tok.empty() && has_digit) {
            try {
                // remove sufixos/ruídos não-numéricos ao final
                size_t l = 0, r = tok.size();
                while (l < r && !(std::isdigit((unsigned char)tok[l]) || tok[l]=='-' || tok[l]=='+')) ++l;
                while (r > l && !std::isdigit((unsigned char)tok[r-1])) --r;
                if (l < r) {
                    long long v = std::stoll(tok.substr(l, r-l));
                    nums.push_back(v);
                }
            } catch (...) { /* ignora token inválido */ }
        }
        tok.clear();
    };

    std::string line;
    line.reserve(256);
    while (std::getline(in, line)) {
        if (is_comment_line(line)) { tok.clear(); continue; }

        // Normaliza vírgulas para espaço
        for (char& ch : line) if (ch == ',') ch = ' ';

        // Varre caractere a caractere
        tok.clear();
        for (size_t i = 0; i < line.size(); ++i) {
            unsigned char ch = (unsigned char)line[i];

            // aceita dígitos sempre
            if (std::isdigit(ch)) { tok.push_back((char)ch); continue; }

            // aceita sinal se vier antes de dígito (ou se token estiver vazio)
            if ((ch=='-' || ch=='+')) {
                // se já temos dígitos no token, finalizar e começar novo sinal
                bool has_digit = false;
                for (char c2 : tok) if (std::isdigit((unsigned char)c2)) { has_digit = true; break; }
                if (has_digit) {
                    flush_tok();
                    tok.push_back((char)ch);
                } else {
                    // sinal no início do token
                    if (!tok.empty()) tok.clear();
                    tok.push_back((char)ch);
                }
                continue;
            }

            // separador: fecha token (se houver)
            flush_tok();
        }
        // fim da linha -> fecha token pendente
        flush_tok();
    }
    return nums;
}

static std::string stem_from_path(const std::string& path) {
    auto p = path;
#ifdef _WIN32
    std::replace(p.begin(), p.end(), '\\', '/');
#endif
    auto pos = p.find_last_of('/');
    std::string base = (pos == std::string::npos) ? p : p.substr(pos+1);
    return base;
}

// -----------------------------------------------------

void KnapsackProblem::carregar(const std::string& filepath) {
    std::vector<long long> a = read_all_numbers(filepath);
    if (a.size() < 4) {
        throw std::runtime_error("Arquivo invalido (poucos numeros): " + filepath);
    }

    nome = stem_from_path(filepath);

    auto try_set = [&](long long N, long long C, const std::vector<long long>& rest) -> bool {
        if (N <= 0 || C <= 0) return false;

        // Caso A: dois vetores (valores e pesos) → tamanho 2*N
        if ((long long)rest.size() == 2 * N) {
            std::vector<long long> v1(rest.begin(), rest.begin() + (size_t)N);
            std::vector<long long> v2(rest.begin() + (size_t)N, rest.end());

            auto all_le_C = [&](const std::vector<long long>& v) {
                for (auto x : v) if (x < 0 || x > C) return false;
                return true;
            };

            auto set_from = [&](const std::vector<long long>& pesos, const std::vector<long long>& valores) -> bool {
                for (auto w : pesos) if (w <= 0 || w > C) return false;
                itens.clear();
                itens.reserve((size_t)N);
                for (long long i = 0; i < N; ++i) itens.push_back(KPItem{ (int)pesos[(size_t)i], valores[(size_t)i] });
                capacidade = (int)C;
                return true;
            };

            if (all_le_C(v1) && !all_le_C(v2)) {
                return set_from(v1, v2); // v1=peso, v2=valor
            } else if (!all_le_C(v1) && all_le_C(v2)) {
                return set_from(v2, v1); // v2=peso, v1=valor
            } else if (all_le_C(v1) && all_le_C(v2)) {
                // ambíguo: assume primeiro = valores, segundo = pesos (NMGE comum)
                return set_from(v2, v1);
            }
        }

        // Caso B: pares intercalados (w,v) ou (v,w)
        if ((long long)rest.size() == 2 * N) {
            std::vector<KPItem> tmp;
            tmp.reserve((size_t)N);

            // Tenta (w,v)
            bool ok_wv = true;
            for (long long i = 0; i < N; ++i) {
                long long w = rest[(size_t)(2*i)];
                long long v = rest[(size_t)(2*i + 1)];
                if (w <= 0 || w > C || v < 0) { ok_wv = false; break; }
                tmp.push_back(KPItem{ (int)w, v });
            }
            if (ok_wv) {
                itens = std::move(tmp);
                capacidade = (int)C;
                return true;
            }

            // Tenta (v,w)
            tmp.clear();
            bool ok_vw = true;
            for (long long i = 0; i < N; ++i) {
                long long v = rest[(size_t)(2*i)];
                long long w = rest[(size_t)(2*i + 1)];
                if (w <= 0 || w > C || v < 0) { ok_vw = false; break; }
                tmp.push_back(KPItem{ (int)w, v });
            }
            if (ok_vw) {
                itens = std::move(tmp);
                capacidade = (int)C;
                return true;
            }
        }

        return false;
    };

    // Tenta (n, C, resto)
    {
        long long N = a[0], C = a[1];
        std::vector<long long> rest(a.begin()+2, a.end());
        if (try_set(N, C, rest)) return;
    }
    // Tenta (C, n, resto)
    {
        long long C = a[0], N = a[1];
        std::vector<long long> rest(a.begin()+2, a.end());
        if (try_set(N, C, rest)) return;
    }
    // Fallback: (C, pares...) → deduz N
    if (a.size() % 2 == 1) { // 1 para C + pares
        long long C = a[0];
        std::vector<long long> rest(a.begin()+1, a.end());
        long long N = (long long)rest.size() / 2;
        if (try_set(N, C, rest)) return;
    }

    throw std::runtime_error("Formato de instancia nao reconhecido: " + filepath);
}

long long KnapsackProblem::calcularValor(const std::vector<int>& selecao) const {
    long long valor = 0;
    for (size_t i = 0; i < selecao.size() && i < itens.size(); ++i) {
        if (selecao[i]) valor += itens[i].valor;
    }
    return valor;
}
