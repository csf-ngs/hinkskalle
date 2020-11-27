<template>
  <v-container>
    <v-row>
      <v-col>
        <h2>Latest Uploads</h2>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" xl="6" v-for="(up, i) in latest" :key="i">
        <v-card height="100%" outlined raised class="upload" 
            :to="{name: 'ContainerDetails', params: { entity: up.container.entityName, collection: up.container.collectionName, container: up.container.name }}">
          <v-card-title class="text-h6">
            {{up.container.fullPath}}
          </v-card-title>
          <v-card-text>
            {{up.container.createdBy}} | {{(up.container.updatedAt || up.container.createdAt) | moment('YYYY-MM-DD HH:mm:ss')}}
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-chip pill class="mr-1" color="pink lighten-4" v-for="tag in up.tags" :key="tag" @click.stop.prevent="copyTag(up.container, tag)">{{tag}}</v-chip>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
<script lang="ts">
import Vue from 'vue';

import { Container } from '../store/models';

export default Vue.extend({
  name: 'LatestContainers',
  mounted() {
    this.loadLatest();
  },
  computed: {
    latest() {
      return this.$store.getters['containers/latest'];
    },
  },
  methods: {
    loadLatest() {
      this.$store.dispatch('containers/latest')
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    copyTag: function(container: Container, tag: string) {
      this.$copyText(`library://${container.entityName}/${container.collectionName}/${container.name}:${tag}`)
        .then(() => this.$store.commit('snackbar/open', "Copied to clipboard."))
    },
  },

});
</script>