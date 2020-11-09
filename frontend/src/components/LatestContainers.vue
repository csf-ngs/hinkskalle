<template>
  <v-container>
    <v-row justify="center">
          <v-col cols="12">
            <h3>Latest Uploads:</h3>
            <v-list nav>
              <v-list-item-group>
                <v-list-item link v-for="(up, i) in latest" :key="i"
                    :to="{name: 'singularityDetail', params: { entity: up.container.entityName, collection: up.container.collectionName, container: up.container.name }}">
                  <v-list-item-content>
                    <v-list-item-title>
                      {{up.container.entityName}}/{{up.container.collectionName}}/{{up.container.name}}
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      {{up.container.createdBy}} | {{(up.container.updatedAt || up.container.createdAt) | moment('YYYY-MM-DD HH:mm:ss')}}
                    </v-list-item-subtitle>
                  </v-list-item-content>
                  <v-list-item-icon>
                      <v-chip color="light-green lighten-2" v-for="tag in up.tags" :key="tag" @click.stop.prevent="copyTag(up.container, tag)">{{tag}}</v-chip>
                  </v-list-item-icon>
                </v-list-item>
              </v-list-item-group>
            </v-list>
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
      this.$store.dispatch('containers/latest');
    },
    copyTag: function(container: Container, tag: string) {
      this.$copyText(`library://${container.entityName}/${container.collectionName}/${container.name}:${tag}`)
        .then(() => this.$store.commit('snackbar/open', "Copied to clipboard."))
    },
  },

});
</script>