#include <iostream>
#include <vector>
#include <string>
#include <tuple>
#include <filesystem>
#include <cstdio>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <iomanip>
#include <climits>

#include "../include/problem.hpp"
#include "../include/as.hpp"
#include "../include/asRank.hpp"
#include "../include/mmas.hpp"
#include "../include/acs.hpp"

namespace fs = std::filesystem;

// parse seguro de inteiro (string -> long long) sem exceptions
static long long parse_ll_str(const std::string& s_in, long long defval) {
    auto is_space = [](char c){ return c==' '||c=='\t'||c=='\r'||c=='\n'; };
    size_t i=0, n=s_in.size();
    while (i<n && is_space(s_in[i])) ++i;
    if (i==n) return defval;
    bool neg=false;
    if (s_in[i]=='+' || s_in[i]=='-'){ neg = (s_in[i]=='-'); ++i; }
    if (i==n || s_in[i]<'0' || s_in[i]>'9') return defval;
    long long val = 0;
    for (; i<n && s_in[i]>='0' && s_in[i]<='9'; ++i){
        int d = s_in[i]-'0';
        if (!neg){
            if (val > (LLONG_MAX - d)/10) return defval; // overflow
            val = val*10 + d;
        } else {
            if (val < (LLONG_MIN + d)/10) return defval; // underflow
            val = val*10 - d;
        }
    }
    while (i<n){
        if (!is_space(s_in[i])) return defval;
        ++i;
    }
    return val;
}

// lista p01..p08 em data/
static std::vector<std::string> listarInstancias() {
    std::vector<std::string> files;
    for (int i = 1; i <= 8; ++i) {
        char buf[16];
        std::snprintf(buf, sizeof(buf), "p%02d", i);
        std::string stem = buf;
        const std::vector<std::string> exts = { ".txt", ".dat", ".kp" };
        for (const auto& ext : exts) {
            std::string p = std::string("data/") + stem + ext;
            if (fs::exists(p) && fs::is_regular_file(p)) { files.push_back(p); break; }
        }
    }
    return files;
}

static std::unordered_map<std::string,long long> loadTargets(const std::string& path) {
    std::unordered_map<std::string,long long> tgt;
    std::ifstream in(path);
    if (!in) return tgt;
    std::string line;
    auto trim = [](std::string s){
        size_t A=s.find_first_not_of(" \t\r\n");
        size_t B=s.find_last_not_of(" \t\r\n");
        if (A==std::string::npos) return std::string();
        return s.substr(A,B-A+1);
    };
    while (std::getline(in, line)) {
        if (line.empty() || line[0]=='#') continue;
        std::istringstream ss(line);
        std::string a,b;
        if (!std::getline(ss, a, ',')) continue;
        if (!std::getline(ss, b, ',')) continue;
        a=trim(a); b=trim(b);
        if (a.empty() || b.empty()) continue;
        long long v = parse_ll_str(b, LLONG_MIN);
        if (v!=LLONG_MIN) tgt[a] = v;
    }
    return tgt;
}

struct RunRec {
    long long value=0, weight=0;
    bool feasible=false;
    double seconds=0.0;
    unsigned int seed=0;
    std::vector<int> sel;
};

static std::tuple<long long,long long,bool>
evalSel(const std::vector<int>& sel, const KnapsackProblem& prob){
    long long V=0,W=0;
    const auto& itens = prob.getItens();
    for (size_t i=0;i<sel.size() && i<itens.size();++i) if (sel[i]) {
        V += itens[i].valor; W += itens[i].peso;
    }
    return {V,W, W<=prob.getCapacidade()};
}

static double mean(const std::vector<double>& v){
    if (v.empty()) return 0.0; double s=0.0; for(double x:v) s+=x; return s/v.size();
}
static double stdev(const std::vector<double>& v){
    if (v.size()<2) return 0.0; double m=mean(v), s2=0.0; for(double x:v) s2+=(x-m)*(x-m); return std::sqrt(s2/(v.size()-1));
}

static void openCSVs(std::ofstream& csvExec, std::ofstream& csvSum){
    fs::create_directories("results");
    csvExec.open("results/execucoes_p01_p08.csv");
    csvSum.open("results/resumo_p01_p08.csv");
    csvExec << "instance,variant,run,seed,value,weight,feasible,seconds,items\n";
    csvSum  << "instance,variant,best_value,best_weight,feasible,best_seconds,mean_seconds,std_seconds,hit_optimal,target,best_seed\n";
}

static std::string itensToString(const std::vector<int>& sel){
    std::ostringstream oss; bool first=true;
    for (size_t i=0;i<sel.size();++i) if (sel[i]) { if(!first) oss<<" "; first=false; oss<<(i+1); }
    if (first) return "-"; return oss.str();
}

static void printResumo(const std::string& var, const KnapsackProblem& prob,
                        const std::vector<RunRec>& runs, long long target,
                        std::ofstream& csvSum) {
    std::vector<double> vals, times;
    vals.reserve(runs.size()); times.reserve(runs.size());
    long long bestV = -1, worstV = (1LL<<60);
    int bestIdx = -1; double sumT=0.0;

    for (size_t i=0;i<runs.size();++i){
        vals.push_back((double)runs[i].value);
        times.push_back(runs[i].seconds);
        sumT+=runs[i].seconds;
        if (runs[i].value > bestV) { bestV = runs[i].value; bestIdx=(int)i; }
        if (runs[i].value < worstV) worstV = runs[i].value;
    }

    std::cout << "\n--- Resultados Finais Consolidados (Media de " << runs.size() << " Execucoes) ---\n";
    std::cout << "Media do Melhor Valor: " << std::fixed << std::setprecision(2) << mean(vals) << "\n";
    std::cout << "Desvio Padrao do Valor: " << std::setprecision(2) << stdev(vals) << "\n";
    std::cout << "Melhor Valor GLOBAL Obtido: " << bestV << "\n";
    std::cout << "Pior Valor GLOBAL Obtido: " << worstV << "\n";
    std::cout << "---------------------------------------------\n";
    std::cout << "Media do Tempo de Execucao: " << std::setprecision(4) << mean(times) << "s\n";
    std::cout << "Desvio Padrao do Tempo: " << std::setprecision(4) << stdev(times) << "s\n";
    std::cout << "---------------------------------------------\n";
    std::cout << "Tempo Total de Todas as " << runs.size() << " Execucoes: " << std::setprecision(4) << sumT << "s\n\n";

    const RunRec& best = runs[bestIdx];
    long long pesoTotal = best.weight;

    std::cout << "--- Detalhes da Melhor Solucao Encontrada GLOBALMENTE ---\n";
    std::cout << "Melhor Valor Alcancado: " << best.value << "\n";
    std::cout << "Itens Incluidos (ID, Peso, Valor):\n";
    const auto& itens = prob.getItens();
    for (size_t i=0;i<best.sel.size() && i<itens.size();++i){
        if (best.sel[i]) {
            std::cout << "- Item " << (i+1) << " (Peso: " << itens[i].peso << ", Valor: " << itens[i].valor << ")\n";
        }
    }
    std::cout << "Peso Total da Solucao: " << pesoTotal << " / " << prob.getCapacidade() << "\n";
    std::cout << "Esta solucao foi encontrada na Execucao " << (bestIdx+1)
              << " (Tempo: " << best.seconds << "s)\n";

    bool hit = (target >= 0 && bestV >= target);
    if (target >= 0) {
        std::cout << "\nAtingiu o otimo conhecido?  " << (hit? "sim":"NAO") << "  | alvo=" << target << "\n";
    } else {
        std::cout << "\nAtingiu o otimo conhecido?  (sem alvo configurado)\n";
    }

    csvSum << prob.getNome() << "," << var << ","
           << best.value << "," << best.weight << ","
           << (best.feasible?1:0) << "," << best.seconds << ","
           << mean(times) << "," << stdev(times) << ","
           << (hit?1:0) << "," << (target>=0?target:0) << ","
           << best.seed << "\n";
}

static void rodarVariante(const std::string& var, const KnapsackProblem& prob,
                          int repeats, unsigned int base_seed,
                          std::vector<RunRec>& out, std::ofstream& csvExec) {
    out.clear(); out.reserve(repeats);

    // Parametros fixos (nao aparecem no console)
    int ants=100, iters=600, w=5;
    double alpha=1.0, beta=3.0, rho=0.1, q0=0.90, xi=0.10;

    std::cout << "\n>>> " << var << " - Execucoes (" << repeats << "x)\n";

    for (int rep=1; rep<=repeats; ++rep) {
        unsigned int seed = base_seed + (unsigned int)rep; // seed distinta por execucao
        std::vector<int> sel;
        auto t0 = std::chrono::high_resolution_clock::now();

        if (var=="AS") {
            AntSystem alg(ants, iters, alpha, beta, rho, seed);
            sel = alg.executar(prob);
        } else if (var=="ASRank") {
            ASRank alg(ants, iters, alpha, beta, rho, w, seed);
            sel = alg.executar(prob);
        } else if (var=="MMAS") {
            MMAS alg(ants, iters, alpha, beta, rho, seed);
            sel = alg.executar(prob);
        } else if (var=="ACS") {
            ACS alg(ants, iters, alpha, beta, rho, q0, xi, seed);
            sel = alg.executar(prob);
        } else {
            throw std::runtime_error("Variante desconhecida: " + var);
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> dt = t1 - t0;

        auto [V,W,ok] = evalSel(sel, prob);

        std::cout << "Execucao " << rep
                  << ": valor=" << V
                  << " peso=" << W
                  << " viavel=" << (ok? "sim":"NAO")
                  << " tempo=" << std::fixed << std::setprecision(4) << dt.count() << "s\n";
        std::cout << "  Itens: ";
        bool first=true; for (size_t k=0;k<sel.size();++k) if (sel[k]) {
            if(!first) std::cout << ", ";
            first=false; std::cout << (k+1);
        }
        if(first) std::cout << "(nenhum)";
        std::cout << "\n";

        RunRec r; r.value=V; r.weight=W; r.feasible=ok; r.seconds=dt.count(); r.seed=seed; r.sel=std::move(sel);
        out.push_back(std::move(r));

        csvExec << prob.getNome() << "," << var << "," << rep << ","
                << seed << "," << V << "," << W << "," << (ok?1:0) << ","
                << dt.count() << "," << itensToString(out.back().sel) << "\n";
    }
}

int main() {
    try {
        auto files = listarInstancias();
        if (files.empty()) { std::cerr << "Nenhuma instancia p01..p08 encontrada em ./data\n"; return 1; }

        auto targets = loadTargets("config/targets.csv");

        std::ofstream csvExec, csvSum;
        openCSVs(csvExec, csvSum);

        const int repeats = 20;
        const unsigned int base_seed = 987654321u; // mude se desejar outra reproducibilidade

        for (const auto& path : files) {
            KnapsackProblem problem(path);
            std::cout << "\n==============================\n";
            std::cout << "Instancia: " << problem.getNome()
                      << " | Capacidade=" << problem.getCapacidade()
                      << " | Itens=" << problem.getItens().size() << "\n";
            std::cout << "==============================\n";

            long long alvo = targets.count(problem.getNome()) ? targets[problem.getNome()] : -1;

            { std::vector<RunRec> runs; rodarVariante("AS", problem, repeats, base_seed, runs, csvExec);
              printResumo("AS", problem, runs, alvo, csvSum); }

            { std::vector<RunRec> runs; rodarVariante("ASRank", problem, repeats, base_seed+100000u, runs, csvExec);
              printResumo("ASRank", problem, runs, alvo, csvSum); }

            { std::vector<RunRec> runs; rodarVariante("MMAS", problem, repeats, base_seed+200000u, runs, csvExec);
              printResumo("MMAS", problem, runs, alvo, csvSum); }

            { std::vector<RunRec> runs; rodarVariante("ACS", problem, repeats, base_seed+300000u, runs, csvExec);
              printResumo("ACS", problem, runs, alvo, csvSum); }
        }

        std::cout << "\nConcluido.\nArquivos salvos em:\n"
                  << " - results/execucoes_p01_p08.csv\n"
                  << " - results/resumo_p01_p08.csv\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Erro: " << e.what() << "\n";
        return 1;
    }
}
