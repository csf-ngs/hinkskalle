<template>
  <v-toolbar flat class="grey lighten-3">
    <v-toolbar-title>{{title}}</v-toolbar-title>
    <slot></slot>
    <v-spacer></v-spacer>
    <v-autocomplete
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
        dense solo flat>
      <template v-slot:item="{ item }">
        <v-list-item-avatar>
          <v-icon v-if="item.value.type=='Entity'">mdi-account-box-multiple</v-icon>
          <v-icon v-if="item.value.type=='Collection'">mdi-folder-multiple</v-icon>
          <v-icon v-if="item.value.type=='Container'">mdi-package</v-icon>
        </v-list-item-avatar>
        <v-list-item-content>
          {{item.value.fullPath}}
        </v-list-item-content>
      </template>
    </v-autocomplete>
    <v-icon>mdi-help-circle-outline</v-icon>
  </v-toolbar>
</template>
<script lang="ts">
import { Collection, Container, Entity, SearchResult } from '@/store/models';
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
    loading(): boolean {
      return this.$store.getters['search/status'] === 'loading';
    },
    result(): any[] {
      const res = this.$store.getters['search/results'] as SearchResult;
      const ret = res ? _flatten([
        [{ header: 'Entities' }],
        _map(res.entity, e => ({ text: e.name, value: _set(e, 'type', 'Entity') })) as any,
        [{ header: 'Collections' }],
        _map(res.collection, e => ({ text: e.name, value: _set(e, 'type', 'Collection') })) as any,
        [{ header: 'Containers' }],
        _map(res.container, e => ({ text: e.name, value: _set(e, 'type', 'Container') })) as any,
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
      switch(obj.type) {
        case 'Entity':
          this.$router.push({ name: 'EntityCollections', params: { entity: obj.entityName }})
          break;
        case 'Collection':
          this.$router.push({ name: 'Containers', params: { entity: obj.entityName, collection: obj.collectionName }})
          break;
        case 'Container':
          this.$router.push({ name: 'ContainerDetails', params: { entity: obj.entityName, collection: obj.collectionName, container: obj.containerName }})
          break;
      }
    },
  },
});
</script>