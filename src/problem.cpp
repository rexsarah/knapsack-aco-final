#include "../include/problem.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <cctype>
#include <string>
#include <vector>
#include <algorithm>

// ================= utilitários =================
static std::string trim(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return std::string();
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

static bool is_int64(const std::string& s) {
    if (s.empty()) return false;
    size_t i = (s[0] == '+' || s[0] == '-') ? 1u : 0u;
    if (i >= s.size()) return false;
    for (; i < s.size(); ++i) if (!std::isdigit(static_cast<unsigned char>(s[i]))) return false;
    return true;
}

static std::vector<std::string> split_ws(const std::string& line) {
    std::vector<std::string> out;
    std::string tok;
    std::istringstream ss(line);
    while (ss >> tok) out.push_back(tok);
    return out;
}

static std::vector<std::string> read_nonempty_lines(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("Nao foi possivel abrir: " + path);
    std::vector<std::string> L;
    std::string raw;
    while (std::getline(in, raw)) {
        std::string s = trim(raw);
        if (!s.empty()) L.push_back(s);
    }
    if (L.empty()) throw std::runtime_error("Arquivo vazio: " + path);
    return L;
}

static std::string stem_from_path(const std::string& p) {
    size_t slash = p.find_last_of("/\\");
    std::string fn = (slash == std::string::npos) ? p : p.substr(slash + 1);
    size_t dot = fn.find_last_of('.');
    return (dot == std::string::npos) ? fn : fn.substr(0, dot);
}

// ============== parser flexível (64-bits) ==============
//
// Aceita automaticamente:
//
// A) "n cap" na 1ª; depois n linhas "p w"
// B) "n" ; "cap" ; depois n linhas "p w"
// C) "n" ; (linha com 2*n tokens: p1..pn w1..wn) ; "cap"
// D) Beasley: "n" ; (linha com n lucros) ; (linha com n pesos) ; "cap"
// E) Jooken:  "n" ; n linhas "p w" ; "cap" na última
// F) (heurística) "cap n" na 1ª e depois pares "p w" em sequência
// G) **Novo**: "cap" ; "n" ; n linhas "p w" (clássicas p01..p07)
//
// Observação: todos os inteiros são lidos como 64-bits.
static void parse_instance_flexible(
    const std::vector<std::string>& L,
    long long& outCap,
    std::vector<Item>& outItems,
    const std::string& pathForErr
) {
    auto bad = [&](const std::string& msg){
        throw std::runtime_error("Arquivo invalido (" + msg + "): " + pathForErr);
    };

    if (L.empty()) bad("vazio");
    auto t0 = split_ws(L[0]);
    if (t0.empty() || !is_int64(t0[0])) bad("cabecalho");

    auto getLL = [](const std::string& s)->long long { return std::stoll(s); };

    // -------- F) "cap n" + pares intercalados (heurística para casos como p08)
    if (t0.size() >= 2 && is_int64(t0[0]) && is_int64(t0[1])) {
        long long a = getLL(t0[0]); // cap?
        long long b = getLL(t0[1]); // n?
        if (a > 100000 && b > 0) {
            // coletar todos os números do restante do arquivo
            std::vector<long long> nums;
            for (size_t i = 1; i < L.size(); ++i) {
                auto toks = split_ws(L[i]);
                for (auto& tk : toks) if (is_int64(tk)) nums.push_back(getLL(tk));
            }
            if (nums.size() >= 2 * static_cast<size_t>(b)) {
                outCap = a;
                outItems.clear(); outItems.reserve(static_cast<size_t>(b));
                size_t k = 0;
                for (long long i = 0; i < b; ++i) {
                    if (k + 1 >= nums.size()) bad("faltaram valores (F)");
                    long long v = nums[k++], w = nums[k++];
                    outItems.push_back({v,w});
                }
                return;
            }
        }
    }

    // -------- A) "n cap" + n linhas "p w"
    if (t0.size() == 2 && is_int64(t0[0]) && is_int64(t0[1])) {
        long long n = getLL(t0[0]);
        long long C = getLL(t0[1]);
        if ((long long)L.size() < 1 + n) bad("faltaram linhas de itens (A)");
        std::vector<Item> items; items.reserve((size_t)n);
        for (long long i = 0; i < n; ++i) {
            auto s = split_ws(L[1 + (size_t)i]);
            if (s.size() < 2 || !is_int64(s[0]) || !is_int64(s[1])) bad("linha de item (A)");
            items.push_back({ getLL(s[0]), getLL(s[1]) });
        }
        outCap = C; outItems = std::move(items);
        return;
    }

    // A partir daqui, primeira linha tem só um número
    long long first = getLL(t0[0]);
    if (L.size() < 2) bad("faltando dados");
    auto t1 = split_ws(L[1]);

    // -------- G) "cap" ; "n" ; n linhas "p w"
    if (t0.size() == 1 && is_int64(t0[0]) && t1.size() == 1 && is_int64(t1[0])) {
        long long C = first;
        long long n = getLL(t1[0]);
        if ((long long)L.size() < 2 + n) bad("faltaram linhas de itens (G)");
        std::vector<Item> items; items.reserve((size_t)n);
        for (long long i = 0; i < n; ++i) {
            auto s = split_ws(L[2 + (size_t)i]);
            if (s.size() < 2 || !is_int64(s[0]) || !is_int64(s[1])) bad("linha de item (G)");
            items.push_back({ getLL(s[0]), getLL(s[1]) });
        }
        outCap = C; outItems = std::move(items);
        return;
    }

    // -------- D) Beasley: "n" ; n lucros ; n pesos ; "cap"
    if ((long long)t1.size() == first && L.size() >= 4) {
        auto t2 = split_ws(L[2]);
        if ((long long)t2.size() == first && is_int64(L[3])) {
            long long C = getLL(L[3]);
            std::vector<Item> items; items.reserve((size_t)first);
            for (long long i = 0; i < first; ++i) {
                items.push_back({ getLL(t1[(size_t)i]), getLL(t2[(size_t)i]) });
            }
            outCap = C; outItems = std::move(items);
            return;
        }
    }

    // -------- C) "n" ; 2*n tokens ; "cap"
    if ((long long)t1.size() == 2*first && L.size() >= 3 && is_int64(L[2])) {
        long long C = getLL(L[2]);
        std::vector<Item> items; items.reserve((size_t)first);
        for (long long i = 0; i < first; ++i) {
            long long p = getLL(t1[(size_t)i]);
            long long w = getLL(t1[(size_t)(first + i)]);
            items.push_back({p,w});
        }
        outCap = C; outItems = std::move(items);
        return;
    }

    // -------- B) "n" ; "cap" ; n linhas "p w"
    if (t1.size() == 1 && is_int64(t1[0])) {
        long long C = getLL(t1[0]);
        if ((long long)L.size() < 2 + first) bad("faltaram linhas de itens (B)");
        std::vector<Item> items; items.reserve((size_t)first);
        for (long long i = 0; i < first; ++i) {
            auto s = split_ws(L[2 + (size_t)i]);
            if (s.size() < 2 || !is_int64(s[0]) || !is_int64(s[1])) bad("linha de item (B)");
            items.push_back({ getLL(s[0]), getLL(s[1]) });
        }
        outCap = C; outItems = std::move(items);
        return;
    }

    // -------- E) "n" ; n linhas "p w" ; "cap" no fim
    if ((long long)L.size() >= 2 + first && is_int64(L.back())) {
        long long C = getLL(L.back());
        std::vector<Item> items; items.reserve((size_t)first);
        for (long long i = 0; i < first; ++i) {
            auto s = split_ws(L[1 + (size_t)i]);
            if (s.size() < 2 || !is_int64(s[0]) || !is_int64(s[1])) bad("linha de item (E)");
            items.push_back({ getLL(s[0]), getLL(s[1]) });
        }
        outCap = C; outItems = std::move(items);
        return;
    }

    bad("formato nao reconhecido");
}

// ================= carregamento =================
void KnapsackProblem::load(const std::string& path) {
    nome_ = stem_from_path(path);
    auto L = read_nonempty_lines(path);

    long long C = 0;
    std::vector<Item> items;
    parse_instance_flexible(L, C, items, path);

    capacidade_ = C;
    itens_ = std::move(items);
}

// ============== utilitários pedidas pelos algos =============
long long KnapsackProblem::calcularValor(const std::vector<int>& selecao) const {
    long long v = 0;
    const auto n = std::min(selecao.size(), itens_.size());
    for (size_t i = 0; i < n; ++i) if (selecao[i]) v += itens_[i].valor;
    return v;
}

long long KnapsackProblem::calcularPeso(const std::vector<int>& selecao) const {
    long long w = 0;
    const auto n = std::min(selecao.size(), itens_.size());
    for (size_t i = 0; i < n; ++i) if (selecao[i]) w += itens_[i].peso;
    return w;
}
