<template>
  <v-toolbar flat class="grey lighten-3">
    <v-toolbar-title>{{title}}</v-toolbar-title>
    <slot></slot>
    <v-spacer></v-spacer>
    <v-autocomplete v-if="isLoggedIn" class="mr-3" style="max-width: 300px"
        v-model="localState.select"
        :loading="loading"
        :items="result"
        :search-input.sync="localState.search"
        hide-no-data
        hide-details
        label="Search..."
        @input="navigate"
        clearable
        append-icon=''
        no-filter
        solo flat>
      <template v-slot:item="{ item }">
        <v-list-item-avatar>
          <v-icon v-if="item.value.ctype=='Entity'">mdi-account-box-multiple</v-icon>
          <v-icon v-else-if="item.value.ctype=='Collection'">mdi-folder-multiple</v-icon>
          <template v-else-if="item.value.ctype=='Container'">
            <img v-if="item.value.type=='docker'" v-bind="attrs" v-on="on" src="/docker-logo.png" style="height: 1.2rem; width: 1.7rem;">
            <img v-else-if="item.value.type=='singularity'" v-bind="attrs" v-on="on" src="/singularity-logo.png" style="height: 1.2rem; width: 1.2rem;">
            <img v-else-if="item.value.type=='generic'" v-bind="attrs" v-on="on" src="/oras-logo.png" style="height: 1.2rem; width: 1.2rem;">
            <v-icon v-bind="attrs" v-on="on" v-else-if="item.value.type=='mixed'">mdi-folder-multiple</v-icon>
          </template>
          <template v-else-if="item.value.ctype=='Image'">
            <img v-if="item.value.type=='docker'" v-bind="attrs" v-on="on" src="/docker-logo.png" style="height: 1.2rem; width: 1.7rem;">
            <img v-else-if="item.value.type=='singularity'" v-bind="attrs" v-on="on" src="/singularity-logo.png" style="height: 1.2rem; width: 1.2rem;">
            <img v-else-if="item.value.type=='oci'" v-bind="attrs" v-on="on" src="/oci-logo.png" style="height: 1.2rem; width: 1.2rem;">
            <v-icon v-bind="attrs" v-on="on" v-else-if="item.value.type=='other'">mdi-file-question</v-icon>
          </template>
        </v-list-item-avatar>
        <v-list-item-content>
          {{item.value.prettyPath}}
        </v-list-item-content>
      </template>
    </v-autocomplete>
    <router-link to="About" class="text-decoration-none">
      <v-icon>mdi-help-circle-outline</v-icon>
    </router-link>
  </v-toolbar>
</template>
<script lang="ts">
import { SearchResult } from '@/store/models';
import Vue from 'vue';

import { flatten as _flatten, map as _map, set as _set } from 'lodash';

interface State {
  search: string | null;
  select: string | null;
}

export default Vue.extend({
  name: 'TopBar',
  props: {
    title: {
      type: String,
      required: true,
    },
  },
  data: function(): { localState: State } {
    return {
      localState: {
        search: null,
        select: null,
      }
    }
  },
  computed: {
    isLoggedIn(): boolean {
      return this.$store.getters.isLoggedIn;
    },
    loading(): boolean {
      return this.$store.getters['search/status'] === 'loading';
    },
    result(): any[] {
      const res = this.$store.getters['search/results'] as SearchResult;
      const ret = res ? _flatten([
        [{ header: 'Entities' }],
        _map(res.entity, e => ({ text: e.name, value: _set(e, 'ctype', 'Entity') })) as any,
        [{ header: 'Collections' }],
        _map(res.collection, e => ({ text: e.name, value: _set(e, 'ctype', 'Collection') })) as any,
        [{ header: 'Containers' }],
        _map(res.container, e => ({ text: e.name, value: _set(e, 'ctype', 'Container') })) as any,
        [{ header: 'Images' }],
        _map(res.image, i => ({ text: i.containerName, value: _set(i, 'ctype', 'Image') })) as any,
      ]) : [];
      return ret;
    },
  },
  watch: {
    'localState.search': function searchState(val: string) {
      if (val) {
        if (val !== this.localState.select && !this.loading) {
          this.search(val);
        }
      }
      else {
        this.$store.commit('search/setResults', null);
      }
    },
  },
  methods: {
    search(val: string) {
      this.$store.dispatch('search/any', { name: val })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    navigate(obj: any) {
      if (!obj) {
        return;
      }
      switch(obj.ctype) {
        case 'Entity':
          this.$router.push({ name: 'EntityCollections', params: { entity: obj.entityName }})
          break;
        case 'Collection':
          this.$router.push({ name: 'Containers', params: { entity: obj.entityName, collection: obj.collectionName }})
          break;
        case 'Container':
        case 'Image':
          this.$router.push({ name: 'ContainerDetails', params: { entity: obj.entityName, collection: obj.collectionName, container: obj.containerName }})
          break;
      }
    },
  },
});
</script>