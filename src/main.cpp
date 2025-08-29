// main.cpp — runner com rótulo único (pasta/arquivo), sem duplicações e com agregado opcional

#include <algorithm>
#include <chrono>
#include <cctype>
#include <climits>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <vector>

#include "../include/problem.hpp"
#include "../include/as.hpp"
#include "../include/asRank.hpp"
#include "../include/mmas.hpp"
#include "../include/acs.hpp"

#include "profiles.h"
#include "cli.hpp"

namespace fs = std::filesystem;

// ---------------- utilitários ----------------
template<class, class = void> struct has_profile_key   : std::false_type {};
template<class T> struct has_profile_key<T, std::void_t<decltype(std::declval<T>().profile_key)>> : std::true_type {};
template<class, class = void> struct has_profile       : std::false_type {};
template<class T> struct has_profile<T, std::void_t<decltype(std::declval<T>().profile)>> : std::true_type {};
template<class, class = void> struct has_perfil        : std::false_type {};
template<class T> struct has_perfil<T, std::void_t<decltype(std::declval<T>().perfil)>> : std::true_type {};

template<class, class = void> struct has_instances_dir : std::false_type {};
template<class T> struct has_instances_dir<T, std::void_t<decltype(std::declval<T>().instances_dir)>> : std::true_type {};
template<class, class = void> struct has_instances     : std::false_type {};
template<class T> struct has_instances<T, std::void_t<decltype(std::declval<T>().instances)>> : std::true_type {};
template<class, class = void> struct has_instancias    : std::false_type {};
template<class T> struct has_instancias<T, std::void_t<decltype(std::declval<T>().instancias)>> : std::true_type {};

template<class, class = void> struct has_algo          : std::false_type {};
template<class T> struct has_algo<T, std::void_t<decltype(std::declval<T>().algo)>> : std::true_type {};
template<class, class = void> struct has_metodo        : std::false_type {};
template<class T> struct has_metodo<T, std::void_t<decltype(std::declval<T>().metodo)>> : std::true_type {};

template<class V>
static inline std::string to_str_any(const V& v) {
    if constexpr (std::is_same_v<V, std::string>) return v;
    else if constexpr (std::is_convertible_v<V, std::string>) return std::string(v);
    else if constexpr (std::is_integral_v<V>) return std::to_string(v);
    else return std::string();
}

template<class T>
static inline std::string get_profile_key(const T& cli) {
    if constexpr (has_profile_key<T>::value)   return to_str_any(cli.profile_key);
    else if constexpr (has_profile<T>::value)  return to_str_any(cli.profile);
    else if constexpr (has_perfil<T>::value)   return to_str_any(cli.perfil);
    else                                       return "1";
}

template<class T>
static inline std::string get_instances_dir(const T& cli) {
    if constexpr (has_instances_dir<T>::value) return to_str_any(cli.instances_dir);
    else if constexpr (has_instances<T>::value)return to_str_any(cli.instances);
    else if constexpr (has_instancias<T>::value)return to_str_any(cli.instancias);
    else                                       return std::string();
}

template<class T>
static inline std::string get_algo(const T& cli) {
    if constexpr (has_algo<T>::value)          return to_str_any(cli.algo);
    else if constexpr (has_metodo<T>::value)   return to_str_any(cli.metodo);
    else                                       return std::string();
}

static std::vector<std::string> read_list(const std::string& path) {
    std::vector<std::string> files;
    std::ifstream in(path);
    if (!in) return files;
    std::string line;
    auto trim = [](std::string s){
        size_t A = s.find_first_not_of(" \t\r\n");
        size_t B = s.find_last_not_of(" \t\r\n");
        if (A == std::string::npos) return std::string();
        return s.substr(A, B - A + 1);
    };
    while (std::getline(in, line)) {
        auto pos = line.find('#');
        if (pos != std::string::npos) line = line.substr(0, pos);
        line = trim(line);
        if (!line.empty()) files.push_back(line);
    }
    return files;
}

static std::unordered_map<std::string,long long> loadTargets(const std::string& path) {
    std::unordered_map<std::string,long long> tgt;
    std::ifstream in(path);
    if (!in) return tgt;

    auto is_int = [](const std::string& s){
        if (s.empty()) return false;
        size_t i = (s[0]=='+'||s[0]=='-')?1u:0u;
        if (i>=s.size()) return false;
        for (; i<s.size(); ++i) if (!std::isdigit((unsigned char)s[i])) return false;
        return true;
    };

    std::string line; bool header=true;
    while (std::getline(in, line)) {
        if (header) { header=false; continue; }
        std::stringstream ss(line);
        std::string name,val;
        if (!std::getline(ss, name, ',')) continue;
        if (!std::getline(ss, val, ',')) continue;
        std::transform(name.begin(), name.end(), name.begin(), [](unsigned char c){return std::tolower(c);});
        if (!is_int(val)) continue;
        try { tgt[name] = std::stoll(val); } catch (...) {}
    }
    return tgt;
}

struct RunRec {
    long long value{0};
    long long weight{0};
    bool feasible{false};
    double seconds{0.0};
    unsigned seed{0};
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
    if (v.empty()) return 0.0;
    double s=0.0; for(double x:v) s+=x; return s/v.size();
}
static double stdev(const std::vector<double>& v){
    if (v.size()<2) return 0.0; double m=mean(v), s2=0.0; for(double x:v) s2+=(x-m)*(x-m); return std::sqrt(s2/(v.size()-1));
}

static std::string itensToString(const std::vector<int>& sel){
    std::ostringstream oss; bool first=true;
    for (size_t i=0;i<sel.size();++i) if (sel[i]) { if(!first) oss<<" "; first=false; oss<<(i+1); }
    return first ? std::string("-") : oss.str();
}

// ---------- abertura de CSVs ----------
static void openAggCSVs(std::ofstream& csvExec, std::ofstream& csvSum){
    fs::create_directories("results/jooken");
    bool newExec = !fs::exists("results/jooken/execucoes_jooken.csv");
    bool newSum  = !fs::exists("results/jooken/resumo_jooken.csv");
    csvExec.open("results/jooken/execucoes_jooken.csv", std::ios::app);
    csvSum.open("results/jooken/resumo_jooken.csv", std::ios::app);
    if (newExec) csvExec << "instance,profile,variant,run,seed,value,weight,feasible,seconds,items\n";
    if (newSum)  csvSum  << "instance,profile,variant,best_value,best_weight,feasible,best_seconds,mean_seconds,std_seconds,hit_optimal,target,best_seed\n";
}

static void openLocalCSVs(const fs::path& outDir, std::ofstream& csvExec, std::ofstream& csvSum){
    fs::create_directories(outDir);
    fs::path execPath = outDir / "execucoes.csv";
    fs::path sumPath  = outDir / "summary.csv";
    bool newExec = !fs::exists(execPath);
    bool newSum  = !fs::exists(sumPath);
    csvExec.open(execPath, std::ios::app);
    csvSum.open(sumPath, std::ios::app);
    if (newExec) csvExec << "instance,profile,variant,run,seed,value,weight,feasible,seconds,items\n";
    if (newSum)  csvSum  << "instance,profile,variant,best_value,best_weight,feasible,best_seconds,mean_seconds,std_seconds,hit_optimal,target,best_seed\n";
}

static void writeResumo(const std::string& instLabel,
                        const std::string& profileLabel,
                        const std::string& var,
                        const std::vector<RunRec>& runs,
                        long long target,
                        std::ofstream& out) {
    std::vector<double> times; times.reserve(runs.size());
    long long bestV = LLONG_MIN; int bestIdx = -1;
    for (size_t i=0;i<runs.size();++i){
        times.push_back(runs[i].seconds);
        if (runs[i].feasible) {
            if (runs[i].value > bestV || (runs[i].value == bestV && bestIdx>=0 && runs[i].seconds < runs[bestIdx].seconds)) {
                bestV = runs[i].value; bestIdx=(int)i;
            }
        }
    }
    if (bestIdx < 0) {
        for (size_t i=0;i<runs.size();++i){
            if (runs[i].value > bestV) { bestV = runs[i].value; bestIdx=(int)i; }
        }
    }
    const RunRec& best = runs[bestIdx];
    bool hit = (target >= 0 && best.value >= target && best.feasible);
    out << instLabel << "," << profileLabel << "," << var << ","
        << best.value << "," << best.weight << ","
        << (best.feasible?1:0) << "," << best.seconds << ","
        << mean(times) << "," << stdev(times) << ","
        << (hit?1:0) << "," << (target>=0?target:0) << ","
        << best.seed << "\n";
}

// ---- wrappers das variantes ----
static std::vector<int> runAS (const KnapsackProblem& prob, const Profile& P, unsigned seed) {
    AntSystem alg(P.common.ants, P.common.iterations, P.common.alpha, P.common.beta, P.common.rho, seed);
    return alg.executar(prob);
}
static std::vector<int> runASRank (const KnapsackProblem& prob, const Profile& P, unsigned seed) {
    ASRank alg(P.common.ants, P.common.iterations, P.common.alpha, P.common.beta, P.common.rho, P.asrank.elite_weight, seed);
    return alg.executar(prob);
}
static std::vector<int> runMMAS (const KnapsackProblem& prob, const Profile& P, unsigned seed) {
    MMAS alg(P.common.ants, P.common.iterations, P.common.alpha, P.common.beta, P.common.rho, seed);
    return alg.executar(prob);
}
static std::vector<int> runACS (const KnapsackProblem& prob, const Profile& P, unsigned seed) {
    ACS alg(P.common.ants, P.common.iterations, P.common.alpha, P.common.beta, P.common.rho, P.acs.q0, P.acs.xi, seed);
    return alg.executar(prob);
}

// ---- executa N vezes e escreve execucoes.csv no "dest" selecionado ----
static void runVariant(const std::string& instLabel,
                       const std::string& profileLabel,
                       const std::string& var,
                       const KnapsackProblem& prob,
                       int repeats, unsigned int base_seed,
                       std::vector<RunRec>& out, std::ofstream& csvExec,
                       const Profile& P) {
    out.clear(); out.reserve(repeats);
    for (int rep=1; rep<=repeats; ++rep) {
        unsigned int seed = base_seed + (unsigned int)rep;
        std::vector<int> sel;
        auto t0 = std::chrono::high_resolution_clock::now();
        if (var=="AS")          sel = runAS(prob, P, seed);
        else if (var=="ASRank") sel = runASRank(prob, P, seed);
        else if (var=="MMAS")   sel = runMMAS(prob, P, seed);
        else if (var=="ACS")    sel = runACS(prob, P, seed);
        else throw std::runtime_error("Unknown variant: " + var);
        auto t1 = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> dt = t1 - t0;
        auto [V,W,ok] = evalSel(sel, prob);
        RunRec r; r.value=V; r.weight=W; r.feasible=ok; r.seconds=dt.count(); r.seed=seed; r.sel=std::move(sel);
        out.push_back(std::move(r));
        csvExec << instLabel << "," << profileLabel << "," << var << "," << rep << ","
                << seed << "," << V << "," << W << "," << (ok?1:0) << ","
                << dt.count() << "," << itensToString(out.back().sel) << "\n";
    }
}

// ---- leitura tolerante de flags ----
static std::string readFlag(int argc, char** argv, const std::vector<std::string>& names) {
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        for (const auto& nm : names) {
            if (a == nm) {
                if (i + 1 < argc) return std::string(argv[i + 1]); // --flag X
            }
            const std::string eq = nm + "=";                       // --flag=X
            if (a.rfind(eq, 0) == 0 && a.size() > eq.size()) {
                return a.substr(eq.size());
            }
        }
    }
    return {};
}
static bool readFlagExists(int argc, char** argv, const std::vector<std::string>& names) {
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        for (const auto& nm : names) {
            if (a == nm) return true;
            const std::string eq = nm + "=";
            if (a.rfind(eq, 0) == 0) return true;
        }
    }
    return false;
}

// ----------------------------- MAIN -----------------------------
int main(int argc, char** argv) {
    try {
        Cli cli = parse_cli(argc, argv);

        // argv > cli > default
        std::string profileKey = readFlag(argc, argv, {"--profile","--perfil","-p"});
        if (profileKey.empty()) profileKey = get_profile_key(cli);
        if (profileKey.empty()) profileKey = "1";

        std::string algoReq = readFlag(argc, argv, {"--algo","--metodo","--variant","--var"});
        if (algoReq.empty()) algoReq = get_algo(cli);

        std::string listPath = readFlag(argc, argv, {"--list","--lista","--list-file"});
        std::string instDir  = readFlag(argc, argv, {"--instances","--instancias"});
        if (instDir.empty()) instDir = get_instances_dir(cli);

        std::string outDirArg = readFlag(argc, argv, {"--output-dir","--out"});
        fs::path outDir = outDirArg;

        bool noAggregate = readFlagExists(argc, argv, {"--no-aggregate","--noagg"});

        int repeats = 20;
        unsigned int base_seed = 12345u;
        if (auto s = readFlag(argc, argv, {"--repeats","--runs"}); !s.empty()) repeats = std::max(1, std::stoi(s));
        if (auto s = readFlag(argc, argv, {"--seed"}); !s.empty()) base_seed = (unsigned int)std::stoul(s);

        // perfis
        auto profiles = get_profiles();
        if (!profiles.count(profileKey)) {
            std::cerr << "Perfil '" << profileKey << "' nao encontrado.\n";
            return 2;
        }
        Profile P = profiles[profileKey];

        // instâncias
        std::vector<std::string> files;
        if (!listPath.empty() && fs::exists(listPath)) {
            files = read_list(listPath);
        }
        if (files.empty() && !instDir.empty() && fs::exists(instDir) && fs::is_directory(instDir)) {
            for (auto& p : fs::recursive_directory_iterator(instDir)) {
                if (!p.is_regular_file()) continue;
                auto ext = p.path().extension().string();
                if (ext==".dat" || ext==".txt" || ext==".kp" || ext==".inst" || ext==".in")
                    files.push_back(p.path().string());
            }
            std::sort(files.begin(), files.end());
        }
        if (files.empty()) {
            const std::string fallback = "config/sets/jooken_all.txt";
            files = read_list(fallback);
            if (files.empty()) {
                std::cerr << "No files found. Use --list <arquivo> OU --instances <pasta>.\n";
                return 1;
            }
        }

        auto targets = loadTargets("config/targets.csv");

        // escolha **única** de destino (sem duplicações)
        enum class Sink { Local, Aggregate, Fallback };
        Sink sink = Sink::Fallback;
        if (!outDir.empty())            sink = Sink::Local;
        else if (!noAggregate)          sink = Sink::Aggregate;
        else                            sink = Sink::Fallback;

        std::ofstream csvExec, csvSum;
        fs::path sinkInfo;

        if (sink == Sink::Local) {
            sinkInfo = outDir;
            openLocalCSVs(outDir, csvExec, csvSum);
        } else if (sink == Sink::Aggregate) {
            sinkInfo = "results/jooken";
            openAggCSVs(csvExec, csvSum);
        } else { // fallback: arquivos na raiz
            sinkInfo = ".";
            bool newExec = !fs::exists("execucoes.csv");
            bool newSum  = !fs::exists("summary.csv");
            csvExec.open("execucoes.csv", std::ios::app);
            csvSum.open ("summary.csv",  std::ios::app);
            if (newExec) csvExec << "instance,profile,variant,run,seed,value,weight,feasible,seconds,items\n";
            if (newSum)  csvSum  << "instance,profile,variant,best_value,best_weight,feasible,best_seconds,mean_seconds,std_seconds,hit_optimal,target,best_seed\n";
        }

        // loop principal
        for (const auto& path : files) {
            // === rótulo único: "pasta/arquivo" ===
            fs::path Pth(path);
            std::string instLabel = (Pth.parent_path().filename().string() + "/" + Pth.filename().string());
            // normaliza p/ minúsculas e separador "/"
            std::transform(instLabel.begin(), instLabel.end(), instLabel.begin(),
                           [](unsigned char c){ return std::tolower(c); });

            KnapsackProblem problem(path);
            if (problem.getItens().empty() || problem.getCapacidade() <= 0) {
                std::cerr << "[WARN] Invalid instance: " << path << "\n";
                continue;
            }

            // alvo: tenta "pasta/arquivo"; se não achar, cai no "arquivo" (compat)
            long long target = -1;
            auto itT = targets.find(instLabel);
            if (itT == targets.end()) {
                std::string onlyFile = Pth.filename().string();
                std::transform(onlyFile.begin(), onlyFile.end(), onlyFile.begin(),
                               [](unsigned char c){ return std::tolower(c); });
                auto it2 = targets.find(onlyFile);
                if (it2 != targets.end()) target = it2->second;
            } else {
                target = itT->second;
            }

            const std::string profileLabel = profileKey;

            auto runOne = [&](const std::string& var, unsigned int varSeed){
                std::vector<RunRec> runs;
                runVariant(instLabel, profileLabel, var, problem, repeats, varSeed, runs, csvExec, P);
                writeResumo(instLabel, profileLabel, var, runs, target, csvSum); // 1x, no mesmo sink
            };

            if (!algoReq.empty()) {
                unsigned int seedOff =
                    (algoReq=="AS" ? 100000u :
                     algoReq=="ASRank" ? 200000u :
                     algoReq=="MMAS" ? 300000u : 400000u);
                runOne(algoReq, base_seed + seedOff);
            } else {
                runOne("AS",     base_seed + 100000u);
                runOne("ASRank", base_seed + 200000u);
                runOne("MMAS",   base_seed + 300000u);
                runOne("ACS",    base_seed + 400000u);
            }
        }

        std::cout << "Done.\n";
        std::cout << "Outputs saved under: " << sinkInfo.string() << "\n";
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
}
