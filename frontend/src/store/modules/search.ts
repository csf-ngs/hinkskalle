import {AxiosError, AxiosResponse} from 'axios';
import { Module } from 'vuex';
import {SearchResult, SearchQuery, plainToSearchResult} from '../models';

export interface State {
  status: '' | 'loading' | 'failed' | 'success';
  results: SearchResult | null;
}

const searchModule: Module<State, any> = {
  namespaced: true,
  state: {
    status: '',
    results: null,
  },
  getters: {
    status: (state): string => state.status,
    results: (state): SearchResult | null => state.results,
  },
  mutations: {
    loading(state: State) {
      state.status = 'loading';
    },
    failed(state: State) {
      state.status = 'failed';
    },
    succeeded(state: State) {
      state.status = 'success';
    },
    setResults(state: State, result: SearchResult) {
      state.results = result;
    },
  },
  actions: {
    any: ({ commit, rootState }, search: SearchQuery): Promise<SearchResult> => {
      return new Promise<SearchResult>((resolve, reject) => {
        commit('loading');
        rootState.backend.get(`/v1/search`, { params: { value: search.name, description: search.description }})
          .then((response: AxiosResponse) => {
            const result = plainToSearchResult(response.data.data);
            commit('succeeded');
            commit('setResults', result);
            resolve(result);
          })
          .catch((err: AxiosError) => {
            commit('failed', err);
            reject(err);
          })
      });
    },
  }
};
export default searchModule;